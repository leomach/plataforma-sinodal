from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Prefetch
from django.shortcuts import get_object_or_404, redirect, render

from apps.eventos.models import Evento
from apps.sessoes.forms import SessaoForm
from apps.sessoes.models import Sessao, Votacao
from apps.sessoes.services import eventlog as log_service
from apps.sessoes.services import quorum as quorum_service
from core import constants


def is_lideranca(user):
    return user.is_superuser or user.tipo == constants.LIDERANCA


def lideranca_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not is_lideranca(request.user):
            messages.error(request, 'Acesso restrito à liderança.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped


@lideranca_required
def lista_sessoes(request, slug):
    evento = get_object_or_404(Evento, slug=slug)
    # annotate substitui sessao.votacoes.count no template (evita N+1)
    sessoes = list(
        Sessao.objects.filter(evento=evento)
        .annotate(votacoes_count=Count('votacoes', distinct=True))
        .order_by('data_hora')
    )
    sessao_ativa = next((s for s in sessoes if s.status in Sessao.STATUS_ATIVOS), None)
    return render(request, 'sessoes/lista.html', {
        'evento': evento,
        'sessoes': sessoes,
        'sessao_ativa': sessao_ativa,
    })


@lideranca_required
def criar_sessao(request, slug):
    evento = get_object_or_404(Evento, slug=slug)
    if request.method == 'POST':
        form = SessaoForm(request.POST, evento=evento)
        if form.is_valid():
            sessao = form.save(commit=False)
            sessao.evento = evento
            sessao.save()
            messages.success(request, f'Sessão "{sessao.nome}" criada com sucesso.')
            return redirect('painel_sessao', slug=slug, sessao_id=sessao.pk)
    else:
        form = SessaoForm(evento=evento)
    return render(request, 'sessoes/form.html', {'evento': evento, 'form': form, 'modo': 'criar'})


@lideranca_required
def editar_sessao(request, slug, sessao_id):
    evento = get_object_or_404(Evento, slug=slug)
    sessao = get_object_or_404(Sessao, pk=sessao_id, evento=evento)
    if sessao.status == Sessao.STATUS_ENCERRADA:
        messages.error(request, 'Sessões encerradas não podem ser editadas.')
        return redirect('painel_sessao', slug=slug, sessao_id=sessao_id)
    if request.method == 'POST':
        form = SessaoForm(request.POST, instance=sessao, evento=evento)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sessão atualizada.')
            return redirect('painel_sessao', slug=slug, sessao_id=sessao_id)
    else:
        form = SessaoForm(instance=sessao, evento=evento)
    return render(request, 'sessoes/form.html', {
        'evento': evento, 'form': form, 'sessao': sessao, 'modo': 'editar',
    })


@lideranca_required
def painel_sessao(request, slug, sessao_id):
    evento = get_object_or_404(Evento, slug=slug)
    sessao = get_object_or_404(Sessao, pk=sessao_id, evento=evento)

    # Uma query com prefetch de votos — evita N+1 em contagem()
    votacoes = list(
        sessao.votacoes
        .prefetch_related('votos')
        .order_by('-criada_em')
    )
    # Filtro em Python — sem queries extras
    votacao_aberta = next((v for v in votacoes if v.status == Votacao.STATUS_ABERTA), None)
    votacao_empatada = next((v for v in votacoes if v.status == Votacao.STATUS_EMPATADA), None)

    # select_related evita N+1 de usuario ao exibir logs no template
    logs = sessao.logs.select_related('usuario').order_by('-timestamp')

    # Passa evento_id — evita query extra dentro de info_quorum
    quorum_info = quorum_service.info_quorum(sessao.pk, evento_id=sessao.evento_id)

    from apps.sessoes.models import MembroDaMesa
    from apps.sessoes.forms import VotacaoForm, EventoLogManualForm, TransferirPresidenciaForm

    # Uma única query para toda a mesa ativa, filtrada em Python
    mesa_list = list(
        sessao.membros_mesa
        .filter(encerrou_em__isnull=True)
        .select_related('inscricao__usuario')
        .order_by('cargo')
    )
    presidente_atual = next((m for m in mesa_list if m.cargo == MembroDaMesa.PRESIDENTE), None)
    outros_membros_mesa = [m for m in mesa_list if m.cargo != MembroDaMesa.PRESIDENTE]

    if presidente_atual:
        can_vote_minerva = (presidente_atual.inscricao.usuario == request.user)
    else:
        can_vote_minerva = True

    transferir_form = TransferirPresidenciaForm(sessao=sessao) if outros_membros_mesa else None

    return render(request, 'sessoes/painel.html', {
        'evento': evento,
        'sessao': sessao,
        'votacoes': votacoes,
        'votacao_aberta': votacao_aberta,
        'votacao_empatada': votacao_empatada,
        'logs': logs,
        'quorum': quorum_info,
        'votacao_form': VotacaoForm(),
        'log_form': EventoLogManualForm(),
        'proxima_transicao': sessao.get_proxima_transicao(),
        'mesa_atual': mesa_list,
        'presidente_atual': presidente_atual,
        'outros_membros_mesa': outros_membros_mesa,
        'can_vote_minerva': can_vote_minerva,
        'transferir_form': transferir_form,
        'membros_extras': sessao.membros_extras or [],
    })


@lideranca_required
def alterar_status(request, slug, sessao_id):
    if request.method != 'POST':
        return redirect('painel_sessao', slug=slug, sessao_id=sessao_id)

    evento = get_object_or_404(Evento, slug=slug)
    sessao = get_object_or_404(Sessao, pk=sessao_id, evento=evento)
    acao = request.POST.get('acao')

    if acao == 'avancar':
        proxima = sessao.get_proxima_transicao()
        if not proxima:
            messages.error(request, 'Não é possível avançar o status desta sessão.')
            return redirect('painel_sessao', slug=slug, sessao_id=sessao_id)

        novo_status, _ = proxima

        # Verifica se já existe outra sessão ativa
        if novo_status in Sessao.STATUS_ATIVOS:
            conflito = Sessao.objects.filter(
                evento=evento,
                status__in=Sessao.STATUS_ATIVOS,
            ).exclude(pk=sessao_id).first()
            if conflito:
                messages.error(
                    request,
                    f'Já existe uma sessão ativa: "{conflito.nome}". Encerre-a primeiro.',
                )
                return redirect('painel_sessao', slug=slug, sessao_id=sessao_id)

        sessao.status = novo_status
        sessao.save(update_fields=['status'])

        if novo_status == Sessao.STATUS_CHAMADA:
            log_service.log_chamada_iniciada(sessao)
        elif novo_status == Sessao.STATUS_ABERTA:
            log_service.log_sessao_aberta(sessao)
        elif novo_status == Sessao.STATUS_ENCERRADA:
            log_service.log_sessao_encerrada(sessao)

        messages.success(request, f'Status alterado para "{sessao.get_status_display()}".')

    elif acao == 'retroceder' and sessao.pode_retroceder():
        sessao.status = Sessao.STATUS_EM_BREVE
        sessao.save(update_fields=['status'])
        log_service.log_chamada_cancelada(sessao)
        messages.info(request, 'Chamada cancelada. Sessão retornou a "Em Breve".')
    else:
        messages.error(request, 'Ação inválida.')

    return redirect('painel_sessao', slug=slug, sessao_id=sessao_id)
