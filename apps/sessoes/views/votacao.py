from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.eventos.models import Evento, Inscricao
from apps.sessoes.forms import VotacaoForm
from apps.sessoes.models import Sessao, Votacao, VotoParticipante
from apps.sessoes.services import eventlog as log_service
from apps.sessoes.views.painel import is_lideranca, lideranca_required
from core import constants


@lideranca_required
def criar_votacao(request, slug, sessao_id):
    evento = get_object_or_404(Evento, slug=slug)
    sessao = get_object_or_404(Sessao, pk=sessao_id, evento=evento)

    if sessao.status != Sessao.STATUS_ABERTA:
        messages.error(request, 'Só é possível criar votações em sessões Abertas.')
        return redirect('painel_sessao', slug=slug, sessao_id=sessao_id)

    if sessao.votacoes.filter(status__in=[Votacao.STATUS_ABERTA, Votacao.STATUS_EMPATADA]).exists():
        messages.error(request, 'Já existe uma votação em andamento nesta sessão.')
        return redirect('painel_sessao', slug=slug, sessao_id=sessao_id)

    if request.method == 'POST':
        form = VotacaoForm(request.POST)
        if form.is_valid():
            votacao = form.save(commit=False)
            votacao.sessao = sessao
            votacao.save()
            log_service.log_votacao_aberta(votacao)
            messages.success(request, f'Votação "{votacao.titulo}" aberta.')
            return redirect('painel_sessao', slug=slug, sessao_id=sessao_id)
    else:
        form = VotacaoForm()

    return render(request, 'sessoes/painel.html', {
        'evento': evento, 'sessao': sessao, 'votacao_form': form,
    })


@lideranca_required
def encerrar_votacao(request, slug, sessao_id, votacao_id):
    if request.method != 'POST':
        return redirect('painel_sessao', slug=slug, sessao_id=sessao_id)

    evento = get_object_or_404(Evento, slug=slug)
    sessao = get_object_or_404(Sessao, pk=sessao_id, evento=evento)
    votacao = get_object_or_404(Votacao, pk=votacao_id, sessao=sessao, status=Votacao.STATUS_ABERTA)
    votacao = Votacao.objects.prefetch_related('votos').get(pk=votacao.pk)

    c = votacao.contagem()

    if c['favor'] == c['contra']:
        votacao.status = Votacao.STATUS_EMPATADA
        votacao.save(update_fields=['status'])
        messages.warning(request, 'Empate detectado. Registre o Voto de Minerva.')
    else:
        votacao.encerrada_em = timezone.now()
        if c['favor'] > c['contra']:
            votacao.resultado = Votacao.RESULTADO_APROVADA
        else:
            votacao.resultado = Votacao.RESULTADO_REJEITADA
        votacao.status = Votacao.STATUS_ENCERRADA
        votacao.save(update_fields=['status', 'resultado', 'encerrada_em'])
        log_service.log_votacao_encerrada(votacao)
        messages.success(request, f'Votação encerrada: {votacao.get_resultado_display()}.')

    return redirect('painel_sessao', slug=slug, sessao_id=sessao_id)


@lideranca_required
def voto_minerva(request, slug, sessao_id, votacao_id):
    if request.method != 'POST':
        return redirect('painel_sessao', slug=slug, sessao_id=sessao_id)

    evento = get_object_or_404(Evento, slug=slug)
    sessao = get_object_or_404(Sessao, pk=sessao_id, evento=evento)
    votacao = get_object_or_404(Votacao, pk=votacao_id, sessao=sessao, status=Votacao.STATUS_EMPATADA)

    from apps.sessoes.models import MembroDaMesa
    presidente = sessao.membros_mesa.filter(
        cargo=MembroDaMesa.PRESIDENTE,
        encerrou_em__isnull=True,
    ).select_related('inscricao__usuario').first()

    if presidente and presidente.inscricao.usuario != request.user:
        messages.error(request, 'Apenas o Presidente da Mesa pode registrar o Voto de Minerva.')
        return redirect('painel_sessao', slug=slug, sessao_id=sessao_id)

    voto_str = request.POST.get('voto_minerva')
    if voto_str not in ('favor', 'contra'):
        messages.error(request, 'Voto de Minerva inválido.')
        return redirect('painel_sessao', slug=slug, sessao_id=sessao_id)

    votacao.voto_minerva_favor = (voto_str == 'favor')
    votacao.minerva_por = request.user
    votacao.resultado = Votacao.RESULTADO_APROVADA if votacao.voto_minerva_favor else Votacao.RESULTADO_REJEITADA
    votacao.status = Votacao.STATUS_ENCERRADA
    votacao.encerrada_em = timezone.now()
    votacao.save(update_fields=['voto_minerva_favor', 'minerva_por', 'resultado', 'status', 'encerrada_em'])

    log_service.log_voto_minerva(votacao)
    messages.success(request, f'Voto de Minerva registrado. Resultado: {votacao.get_resultado_display()}.')
    return redirect('painel_sessao', slug=slug, sessao_id=sessao_id)


@login_required
def resultado_votacao(request, slug, sessao_id, votacao_id):
    evento = get_object_or_404(Evento, slug=slug)
    sessao = get_object_or_404(Sessao, pk=sessao_id, evento=evento)
    votacao = get_object_or_404(
        Votacao.objects.prefetch_related('votos'), pk=votacao_id, sessao=sessao
    )
    return render(request, 'sessoes/partials/resultado_votacao.html', {
        'votacao': votacao,
        'contagem': votacao.contagem(),
        'sessao': sessao,
        'slug': slug,
    })


@require_POST
@login_required
def registrar_voto(request, slug, votacao_id):
    evento = get_object_or_404(Evento, slug=slug)
    votacao = get_object_or_404(Votacao, pk=votacao_id, sessao__evento=evento, status=Votacao.STATUS_ABERTA)

    inscricao = Inscricao.objects.filter(
        usuario=request.user,
        evento=evento,
        status=constants.STATUS_APROVADO,
        papel_evento__in=[constants.PAPEL_DELEGADO, constants.PAPEL_EX_OFFICIO],
    ).first()

    if not inscricao:
        messages.error(request, 'Você não tem permissão para votar neste evento.')
        return redirect('hub_evento', slug=slug)

    if VotoParticipante.objects.filter(votacao=votacao, inscricao=inscricao).exists():
        messages.warning(request, 'Você já registrou seu voto nesta votação.')
        return redirect('hub_evento', slug=slug)

    voto_str = request.POST.get('voto')
    mapa = {'favor': VotoParticipante.VOTO_FAVOR, 'contra': VotoParticipante.VOTO_CONTRA, 'abster': VotoParticipante.VOTO_ABSTER}

    if voto_str not in mapa:
        messages.error(request, 'Voto inválido.')
        return redirect('hub_evento', slug=slug)

    VotoParticipante.objects.create(
        votacao=votacao,
        inscricao=inscricao,
        voto=mapa[voto_str],
    )
    messages.success(request, 'Voto registrado com sucesso.')
    return redirect('hub_evento', slug=slug)
