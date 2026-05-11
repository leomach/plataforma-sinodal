import json
import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.urls import reverse
from django.utils import timezone
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings

from .models import Evento, Inscricao, CampoEvento, RespostaInscricao, Sessao, Presenca
from .forms import InscricaoForm, EventoForm, CampoEventoFormSet
from . import emails
from .services import infinitepay as ip_service
from core import constants

logger = logging.getLogger(__name__)


def is_lideranca(user):
    return user.is_superuser or user.tipo == constants.LIDERANCA


def _verificar_pagamento_infinitepay(inscricao):
    """Auxiliar para verificar status no InfinitePay e atualizar inscrição."""
    if not inscricao or inscricao.pago or inscricao.evento.tipo_financeiro != constants.INFINITEPAY:
        return False

    try:
        resultado = ip_service.payment_check(inscricao)
        if resultado.get('paid'):
            status_anterior = inscricao.status
            inscricao.pago = True
            inscricao.data_pagamento = timezone.now()
            inscricao.save()
            emails.enviar_pagamento_confirmado(inscricao)
            if inscricao.status == constants.STATUS_APROVADO and status_anterior != constants.STATUS_APROVADO:
                emails.enviar_inscricao_aprovada(inscricao)
            return True
    except Exception:
        logger.exception('Falha ao verificar status do pagamento InfinitePay para inscrição %s', inscricao.id)
    return False


def lista_eventos(request):
    eventos_ativos = Evento.objects.filter(ativo=True).order_by('-data_inicio')
    return render(request, 'eventos/lista.html', {'eventos': eventos_ativos})


def detalhe_evento(request, slug):
    evento = get_object_or_404(Evento, slug=slug)
    inscricao = None
    if request.user.is_authenticated:
        inscricao = Inscricao.objects.filter(usuario=request.user, evento=evento).first()
        
        # Verifica se já pagou se estiver pendente no InfinitePay
        if inscricao and not inscricao.pago and evento.tipo_financeiro == constants.INFINITEPAY:
            if _verificar_pagamento_infinitepay(inscricao):
                messages.success(request, 'Seu pagamento foi confirmado!')
                inscricao.refresh_from_db()

    agora = timezone.now()
    pre_inscricao = evento.inscricoes_inicio and agora < evento.inscricoes_inicio

    return render(request, 'eventos/detalhe.html', {
        'evento': evento,
        'inscricao': inscricao,
        'ja_inscrito': inscricao is not None,
        'pre_inscricao': pre_inscricao,
        'MANUAL': constants.MANUAL,
        'INFINITEPAY': constants.INFINITEPAY,
        'STATUS_APROVADO': constants.STATUS_APROVADO,
        'STATUS_REJEITADO': constants.STATUS_REJEITADO,
    })


@login_required
@transaction.atomic
def inscrever_evento(request, slug):
    evento = get_object_or_404(Evento.objects.select_for_update(), slug=slug, ativo=True)

    # Verifica se o perfil está completo antes de permitir a inscrição
    if not request.user.perfil_completo:
        messages.warning(request, 'Por favor, complete seu perfil (Nome, E-mail e WhatsApp) antes de se inscrever.')
        return redirect('perfil')

    if Inscricao.objects.filter(usuario=request.user, evento=evento).exists():
        messages.warning(request, 'Você já está inscrito neste evento.')
        return redirect('detalhe_evento', slug=slug)

    if not evento.periodo_inscricao_aberto:
        messages.error(request, 'O período de inscrições para este evento não está aberto.')
        return redirect('detalhe_evento', slug=slug)

    if evento.esgotado:
        messages.error(request, 'Desculpe, as vagas para este evento acabaram.')
        return redirect('detalhe_evento', slug=slug)

    if request.method == 'POST':
        form = InscricaoForm(request.POST, evento=evento)
        if form.is_valid():
            inscricao = form.save(commit=False)
            inscricao.usuario = request.user
            inscricao.evento = evento
            inscricao.save()
            form.save_custom_fields(inscricao)

            if inscricao.status == constants.STATUS_APROVADO:
                emails.enviar_inscricao_aprovada(inscricao)

            # Gera link InfinitePay se aplicável (sem bloquear a inscrição em caso de falha)
            if evento.tipo_financeiro == constants.INFINITEPAY and not inscricao.pago:
                try:
                    redirect_url = request.build_absolute_uri(
                        reverse('confirmacao_inscricao', kwargs={'slug': slug})
                    )
                    webhook_url = request.build_absolute_uri(
                        reverse('webhook_infinitepay', kwargs={'token': settings.INFINITEPAY_WEBHOOK_SECRET})
                    )
                    resultado = ip_service.criar_link(inscricao, redirect_url, webhook_url)
                    Inscricao.objects.filter(pk=inscricao.pk).update(
                        infinitepay_url=resultado.get('url', ''),
                        infinitepay_link_id=resultado.get('slug', '')
                    )
                    inscricao.infinitepay_url = resultado.get('url', '')
                    inscricao.infinitepay_link_id = resultado.get('slug', '')
                except Exception:
                    logger.exception('Falha ao criar link InfinitePay para inscrição %s', inscricao.id)

            return redirect('confirmacao_inscricao', slug=slug)
    else:
        form = InscricaoForm(evento=evento)

    return render(request, 'eventos/inscrever.html', {'evento': evento, 'form': form})


@login_required
def confirmacao_inscricao(request, slug):
    evento = get_object_or_404(Evento, slug=slug)
    inscricao = Inscricao.objects.filter(usuario=request.user, evento=evento).first()
    if not inscricao:
        messages.warning(request, 'Você não possui inscrição neste evento.')
        return redirect('detalhe_evento', slug=slug)

    # Se for InfinitePay e ainda não constar como pago, tenta verificar o status
    if evento.tipo_financeiro == constants.INFINITEPAY and not inscricao.pago:
        # Tenta capturar o slug da InfinitePay se vier na URL e não tivermos gravado ainda
        ip_slug = request.GET.get('slug')
        if ip_slug and not inscricao.infinitepay_link_id:
            inscricao.infinitepay_link_id = ip_slug
            inscricao.save()

        if _verificar_pagamento_infinitepay(inscricao):
            messages.success(request, 'Pagamento confirmado com sucesso!')
            inscricao.refresh_from_db()

    return render(request, 'eventos/confirmacao.html', {
        'evento': evento,
        'inscricao': inscricao,
        'MANUAL': constants.MANUAL,
        'INFINITEPAY': constants.INFINITEPAY,
        'PAPEL_DELEGADO': constants.PAPEL_DELEGADO,
        'PAPEL_EX_OFFICIO': constants.PAPEL_EX_OFFICIO,
    })


@login_required
@user_passes_test(is_lideranca)
def gerenciar_eventos(request):
    eventos = Evento.objects.all().order_by('-data_inicio')
    return render(request, 'eventos/gerenciar.html', {'eventos': eventos})


@login_required
@user_passes_test(is_lideranca)
def criar_evento(request):
    if request.method == 'POST':
        form = EventoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Evento criado com sucesso!')
            return redirect('gerenciar_eventos')
    else:
        form = EventoForm()
    return render(request, 'eventos/form_evento.html', {'form': form, 'titulo': 'Novo Evento'})


@login_required
@user_passes_test(is_lideranca)
def editar_evento(request, slug):
    evento = get_object_or_404(Evento, slug=slug)
    if request.method == 'POST':
        form = EventoForm(request.POST, request.FILES, instance=evento)
        if form.is_valid():
            form.save()
            messages.success(request, 'Evento atualizado com sucesso!')
            return redirect('gerenciar_eventos')
    else:
        form = EventoForm(instance=evento)
    return render(request, 'eventos/form_evento.html', {'form': form, 'titulo': 'Editar Evento', 'evento': evento})


@login_required
@user_passes_test(is_lideranca)
def gerenciar_campos_evento(request, slug):
    evento = get_object_or_404(Evento, slug=slug)
    if request.method == 'POST':
        formset = CampoEventoFormSet(request.POST, instance=evento)
        if formset.is_valid():
            formset.save()
            messages.success(request, 'Formulário de inscrição atualizado com sucesso!')
            return redirect('gerenciar_eventos')
    else:
        formset = CampoEventoFormSet(instance=evento)
    return render(request, 'eventos/gerenciar_campos.html', {'evento': evento, 'formset': formset})


@login_required
@user_passes_test(is_lideranca)
def gerenciar_inscricoes(request, slug):
    evento = get_object_or_404(Evento, slug=slug)
    filtro = request.GET.get('filtro', '')
    inscricoes = Inscricao.objects.filter(evento=evento).select_related('usuario').order_by('-data_inscricao')

    if filtro == 'pendente_pagamento':
        inscricoes = inscricoes.filter(pago=False).exclude(status=constants.STATUS_REJEITADO)
    elif filtro == 'credencial_pendente':
        inscricoes = inscricoes.filter(
            credencial_validada=False,
            papel_evento__in=[constants.PAPEL_DELEGADO, constants.PAPEL_EX_OFFICIO],
        ).exclude(status=constants.STATUS_REJEITADO)
    elif filtro == 'aprovados':
        inscricoes = inscricoes.filter(status=constants.STATUS_APROVADO)
    elif filtro == 'rejeitados':
        inscricoes = inscricoes.filter(status=constants.STATUS_REJEITADO)

    return render(request, 'eventos/inscricoes.html', {
        'evento': evento,
        'inscricoes': inscricoes,
        'filtro_ativo': filtro,
        'MANUAL': constants.MANUAL,
        'INFINITEPAY': constants.INFINITEPAY,
        'PAPEL_DELEGADO': constants.PAPEL_DELEGADO,
        'PAPEL_EX_OFFICIO': constants.PAPEL_EX_OFFICIO,
        'STATUS_APROVADO': constants.STATUS_APROVADO,
        'STATUS_REJEITADO': constants.STATUS_REJEITADO,
    })


@login_required
@user_passes_test(is_lideranca)
def confirmar_pagamento(request, inscricao_id):
    inscricao = get_object_or_404(Inscricao, id=inscricao_id)

    if not inscricao.pago:
        status_anterior = inscricao.status
        inscricao.pago = True
        inscricao.data_pagamento = timezone.now()
        inscricao.validado_por = request.user
        if inscricao.status == constants.STATUS_REJEITADO:
            inscricao.status = constants.STATUS_PENDENTE
        inscricao.save()

        emails.enviar_pagamento_confirmado(inscricao)
        if inscricao.status == constants.STATUS_APROVADO and status_anterior != constants.STATUS_APROVADO:
            emails.enviar_inscricao_aprovada(inscricao)

        messages.success(request, f'Pagamento de {inscricao.usuario.short_name} confirmado.')
    else:
        messages.info(request, 'Pagamento já havia sido confirmado.')

    return redirect('gerenciar_inscricoes', slug=inscricao.evento.slug)


@login_required
@user_passes_test(is_lideranca)
def validar_credencial(request, inscricao_id):
    inscricao = get_object_or_404(Inscricao, id=inscricao_id)

    if not inscricao.credencial_validada:
        status_anterior = inscricao.status
        inscricao.credencial_validada = True
        inscricao.validado_por = request.user
        if inscricao.status == constants.STATUS_REJEITADO:
            inscricao.status = constants.STATUS_PENDENTE
        inscricao.save()

        emails.enviar_credencial_validada(inscricao)
        if inscricao.status == constants.STATUS_APROVADO and status_anterior != constants.STATUS_APROVADO:
            emails.enviar_inscricao_aprovada(inscricao)

        messages.success(request, f'Credencial de {inscricao.usuario.short_name} validada.')
    else:
        messages.info(request, 'Credencial já havia sido validada.')

    return redirect('gerenciar_inscricoes', slug=inscricao.evento.slug)


@login_required
@user_passes_test(is_lideranca)
def rejeitar_inscricao(request, inscricao_id):
    inscricao = get_object_or_404(Inscricao, id=inscricao_id)
    if inscricao.status != constants.STATUS_REJEITADO:
        motivo = request.POST.get('motivo') or request.GET.get('motivo')
        inscricao.status = constants.STATUS_REJEITADO
        if motivo:
            inscricao.motivo_rejeicao = motivo
        inscricao.save()
        messages.warning(request, f'Inscrição de {inscricao.usuario.short_name} rejeitada.')
    return redirect('gerenciar_inscricoes', slug=inscricao.evento.slug)


@login_required
@user_passes_test(is_lideranca)
def reativar_inscricao(request, inscricao_id):
    inscricao = get_object_or_404(Inscricao, id=inscricao_id)
    if inscricao.status == constants.STATUS_REJEITADO:
        inscricao.status = constants.STATUS_PENDENTE
        inscricao.save()
        messages.success(request, f'Inscrição de {inscricao.usuario.short_name} reativada.')
    return redirect('gerenciar_inscricoes', slug=inscricao.evento.slug)


@login_required
def gerar_link_pagamento(request, inscricao_id):
    inscricao = get_object_or_404(Inscricao, id=inscricao_id, usuario=request.user)
    evento = inscricao.evento

    if inscricao.pago or evento.tipo_financeiro != constants.INFINITEPAY:
        return redirect('confirmacao_inscricao', slug=evento.slug)

    # Verifica se já pagou antes de tentar gerar novo link
    if _verificar_pagamento_infinitepay(inscricao):
        messages.info(request, 'Seu pagamento já foi confirmado.')
        return redirect('confirmacao_inscricao', slug=evento.slug)

    try:
        redirect_url = request.build_absolute_uri(
            reverse('confirmacao_inscricao', kwargs={'slug': evento.slug})
        )
        webhook_url = request.build_absolute_uri(
            reverse('webhook_infinitepay', kwargs={'token': settings.INFINITEPAY_WEBHOOK_SECRET})
        )
        resultado = ip_service.criar_link(inscricao, redirect_url, webhook_url)
        new_url = resultado.get('url', '')
        new_slug = resultado.get('slug', '')
        Inscricao.objects.filter(pk=inscricao.pk).update(
            infinitepay_url=new_url,
            infinitepay_link_id=new_slug
        )
        inscricao.infinitepay_url = new_url
        inscricao.infinitepay_link_id = new_slug
    except Exception:
        logger.exception('Falha ao gerar link InfinitePay para inscrição %s', inscricao.id)
        messages.error(request, 'Não foi possível gerar o link de pagamento. Tente novamente.')
        return redirect('confirmacao_inscricao', slug=evento.slug)

    if inscricao.infinitepay_url:
        return redirect(inscricao.infinitepay_url)

    return redirect('confirmacao_inscricao', slug=evento.slug)


@csrf_exempt
@require_POST
def webhook_infinitepay(request, token):
    if token != settings.INFINITEPAY_WEBHOOK_SECRET:
        raise Http404

    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'error': 'invalid payload'}, status=400)

    order_nsu = payload.get('order_nsu', '')
    if not order_nsu.startswith('inscricao-'):
        return JsonResponse({'ok': True})

    try:
        inscricao_id = int(order_nsu.split('-', 1)[1])
        inscricao = Inscricao.objects.select_related('usuario', 'evento').get(pk=inscricao_id)
    except (ValueError, Inscricao.DoesNotExist):
        return JsonResponse({'ok': True})

    if inscricao.pago:
        return JsonResponse({'ok': True})

    # O webhook só é disparado pela InfinitePay quando o pagamento é aprovado,
    # portanto podemos confirmar diretamente sem consulta adicional.
    invoice_slug = payload.get('invoice_slug', '')
    if invoice_slug and not inscricao.infinitepay_link_id:
        Inscricao.objects.filter(pk=inscricao.pk).update(infinitepay_link_id=invoice_slug)
        inscricao.infinitepay_link_id = invoice_slug

    status_anterior = inscricao.status
    inscricao.pago = True
    inscricao.data_pagamento = timezone.now()
    inscricao.save()
    emails.enviar_pagamento_confirmado(inscricao)
    if inscricao.status == constants.STATUS_APROVADO and status_anterior != constants.STATUS_APROVADO:
        emails.enviar_inscricao_aprovada(inscricao)

    return JsonResponse({'ok': True})


@login_required
@transaction.atomic
def editar_inscricao(request, slug):
    evento = get_object_or_404(Evento, slug=slug, ativo=True)
    inscricao = get_object_or_404(Inscricao.objects.select_for_update(), usuario=request.user, evento=evento)

    # Bloqueia edição se já estiver aprovado
    if inscricao.status == constants.STATUS_APROVADO:
        messages.error(request, 'Inscrições aprovadas não podem ser editadas.')
        return redirect('confirmacao_inscricao', slug=slug)

    if request.method == 'POST':
        form = InscricaoForm(request.POST, instance=inscricao, evento=evento)
        if form.is_valid():
            inscricao = form.save(commit=False)
            
            # Se estava rejeitado, volta para pendente ao editar
            if inscricao.status == constants.STATUS_REJEITADO:
                inscricao.status = constants.STATUS_PENDENTE
                
            inscricao.save()
            form.save_custom_fields(inscricao)

            messages.success(request, 'Sua inscrição foi atualizada com sucesso!')
            return redirect('confirmacao_inscricao', slug=slug)
    else:
        form = InscricaoForm(instance=inscricao, evento=evento)

    return render(request, 'eventos/inscrever.html', {
        'evento': evento, 
        'form': form,
        'inscricao': inscricao
    })


@login_required
def hub_evento(request, slug):
    evento = get_object_or_404(Evento, slug=slug)
    inscricao = get_object_or_404(Inscricao, usuario=request.user, evento=evento)

    if inscricao.status != constants.STATUS_APROVADO:
        messages.error(request, 'Você precisa ter sua inscrição aprovada para acessar o Hub.')
        return redirect('detalhe_evento', slug=slug)

    documentos = evento.documentos.all()
    if inscricao.papel_evento not in [constants.PAPEL_DELEGADO, constants.PAPEL_EX_OFFICIO]:
        documentos = documentos.filter(restrito_delegados=False)

    return render(request, 'eventos/hub.html', {
        'evento': evento,
        'inscricao': inscricao,
        'documentos': documentos,
    })
