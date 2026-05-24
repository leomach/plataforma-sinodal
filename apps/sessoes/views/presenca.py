import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.eventos.models import Evento, Inscricao
from apps.sessoes.models import CredencialQRCode, Presenca, Sessao
from apps.sessoes.services import eventlog as log_service
from apps.sessoes.services import quorum as quorum_service
from apps.sessoes.views.painel import is_lideranca, lideranca_required
from core import constants


@lideranca_required
def leitor_presenca(request, slug, sessao_id):
    evento = get_object_or_404(Evento, slug=slug)
    sessao = get_object_or_404(Sessao, pk=sessao_id, evento=evento)
    quorum_info = quorum_service.info_quorum(sessao.pk, evento_id=sessao.evento_id)
    return render(request, 'sessoes/leitor.html', {
        'evento': evento,
        'sessao': sessao,
        'quorum': quorum_info,
    })


@require_POST
@login_required
def toggle_presenca(request, slug, sessao_id):
    if not is_lideranca(request.user):
        return JsonResponse({'ok': False, 'erro': 'Acesso não autorizado.'}, status=403)

    evento = get_object_or_404(Evento, slug=slug)
    sessao = get_object_or_404(Sessao, pk=sessao_id, evento=evento)

    if sessao.status not in [Sessao.STATUS_CHAMADA, Sessao.STATUS_ABERTA]:
        return JsonResponse(
            {'ok': False, 'erro': 'A sessão não está aceitando presenças.'},
            status=400,
        )

    try:
        data = json.loads(request.body)
        token = data.get('token', '').strip()
    except (json.JSONDecodeError, AttributeError):
        token = request.POST.get('token', '').strip()

    if not token:
        return JsonResponse({'ok': False, 'erro': 'Token não fornecido.'}, status=400)

    try:
        credencial = CredencialQRCode.objects.select_related(
            'inscricao__usuario', 'inscricao__evento'
        ).get(token=token, ativo=True)
    except CredencialQRCode.DoesNotExist:
        return JsonResponse({'ok': False, 'erro': 'QR Code inválido ou inativo.'}, status=400)

    inscricao = credencial.inscricao

    if inscricao.evento_id != evento.pk:
        return JsonResponse({'ok': False, 'erro': 'QR Code não pertence a este evento.'}, status=400)

    if inscricao.status != constants.STATUS_APROVADO:
        return JsonResponse({'ok': False, 'erro': 'Inscrição não aprovada.'}, status=400)

    presenca, _ = Presenca.objects.get_or_create(sessao=sessao, inscricao=inscricao)

    # Uma única chamada antes do toggle — captura estado atual
    quorum_info_antes = quorum_service.info_quorum(sessao.pk, evento_id=sessao.evento_id)
    era_presente = presenca.presente

    presenca.presente = not presenca.presente
    presenca.save(update_fields=['presente', 'ultima_atualizacao'])

    nome = inscricao.usuario.get_full_name() or inscricao.usuario.username

    if presenca.presente:
        log_service.log_entrada(sessao, inscricao)
        # Calcula novo quórum via delta — sem query adicional
        quorum_info = quorum_service.calcular_info_quorum_delta(quorum_info_antes, +1)
        if quorum_info['atingido'] and not quorum_info_antes['atingido']:
            log_service.log_quorum_atingido(sessao)
    else:
        log_service.log_saida(sessao, inscricao)
        quorum_info = quorum_service.calcular_info_quorum_delta(quorum_info_antes, -1)

    return JsonResponse({
        'ok': True,
        'nome': nome,
        'papel': inscricao.get_papel_evento_display(),
        'presente': presenca.presente,
        'quorum': quorum_info,
    })


@login_required
def contagem_presenca(request, slug, sessao_id):
    evento = get_object_or_404(Evento, slug=slug)
    sessao = get_object_or_404(Sessao, pk=sessao_id, evento=evento)
    quorum_info = quorum_service.info_quorum(sessao.pk, evento_id=sessao.evento_id)
    return render(request, 'sessoes/partials/quorum.html', {
        'quorum': quorum_info,
        'sessao': sessao,
    })


@lideranca_required
def regenerar_qrcode(request, slug, inscricao_id):
    if request.method != 'POST':
        return redirect('gerenciar_inscricoes', slug=slug)

    evento = get_object_or_404(Evento, slug=slug)
    inscricao = get_object_or_404(
        Inscricao,
        pk=inscricao_id,
        evento=evento,
        papel_evento__in=[constants.PAPEL_DELEGADO, constants.PAPEL_EX_OFFICIO],
    )
    from apps.sessoes.services.qrcode import invalidar_e_regenerar
    invalidar_e_regenerar(inscricao)
    messages.success(request, f'QR Code de {inscricao.usuario.get_full_name()} regenerado com sucesso.')
    return redirect('gerenciar_inscricoes', slug=slug)
