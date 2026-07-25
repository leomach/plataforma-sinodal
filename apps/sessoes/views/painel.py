from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Prefetch
from django.shortcuts import get_object_or_404, redirect, render

from apps.eventos.models import Evento
from apps.sessoes.forms import OperadorPresencaForm, SessaoForm
from apps.sessoes.models import MembroDaMesa, OperadorPresenca, Presenca, Sessao, Votacao
from apps.sessoes.services import eventlog as log_service
from apps.sessoes.services import quorum as quorum_service
from core import constants


def is_lideranca(user):
    return user.is_superuser or user.tipo == constants.LIDERANCA


def is_operador_presenca(user, evento):
    """Inscrito aprovado designado para operar o leitor de presença do evento."""
    if not user.is_authenticated:
        return False
    return OperadorPresenca.objects.filter(
        inscricao__evento=evento,
        inscricao__usuario=user,
    ).exists()


def pode_operar_leitor(user, evento):
    """Liderança OU operador designado do evento."""
    return is_lideranca(user) or is_operador_presenca(user, evento)


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


def _copiar_da_sessao_anterior(sessao_nova, referencia, copiar_presentes, copiar_mesa):
    """Traz presentes e/ou mesa diretora de uma sessão de referência para a nova."""
    if copiar_presentes:
        inscricao_ids = list(
            Presenca.objects.filter(sessao=referencia, presente=True)
            .values_list('inscricao_id', flat=True)
        )
        if inscricao_ids:
            Presenca.objects.bulk_create(
                [Presenca(sessao=sessao_nova, inscricao_id=iid, presente=True) for iid in inscricao_ids],
                ignore_conflicts=True,
            )
            log_service.log_presencas_importadas(
                sessao_nova, len(inscricao_ids), referencia.nome,
            )

    if copiar_mesa:
        membros_ref = list(
            referencia.membros_mesa.filter(encerrou_em__isnull=True).order_by('cargo')
        )
        novos = MembroDaMesa.objects.bulk_create(
            [MembroDaMesa(sessao=sessao_nova, inscricao_id=m.inscricao_id, cargo=m.cargo)
             for m in membros_ref]
        )
        extras = referencia.membros_extras or []
        if extras:
            sessao_nova.membros_extras = extras
            sessao_nova.save(update_fields=['membros_extras'])
        if novos or extras:
            log_service.log_mesa_composta(sessao_nova, novos, extras)


@lideranca_required
def criar_sessao(request, slug):
    evento = get_object_or_404(Evento, slug=slug)
    # Sessão mais recente do evento — origem para copiar presentes/mesa, se desejado.
    sessao_referencia = Sessao.objects.filter(evento=evento).order_by('-data_hora').first()
    if request.method == 'POST':
        form = SessaoForm(request.POST, evento=evento, sessao_referencia=sessao_referencia)
        if form.is_valid():
            sessao = form.save(commit=False)
            sessao.evento = evento
            sessao.save()
            if sessao_referencia:
                _copiar_da_sessao_anterior(
                    sessao,
                    sessao_referencia,
                    form.cleaned_data.get('copiar_presentes'),
                    form.cleaned_data.get('copiar_mesa'),
                )
            messages.success(request, f'Sessão "{sessao.nome}" criada com sucesso.')
            return redirect('painel_sessao', slug=slug, sessao_id=sessao.pk)
    else:
        form = SessaoForm(evento=evento, sessao_referencia=sessao_referencia)
    return render(request, 'sessoes/form.html', {
        'evento': evento,
        'form': form,
        'modo': 'criar',
        'sessao_referencia': sessao_referencia,
    })


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


@lideranca_required
def gerenciar_operadores(request, slug):
    """Liderança designa/remove inscritos que podem operar o leitor de presença.

    O acesso concedido vale para todas as sessões do evento e dá ao operador
    apenas o leitor — nunca o painel, votações, mesa ou logs.
    """
    evento = get_object_or_404(Evento, slug=slug)

    if request.method == 'POST':
        form = OperadorPresencaForm(request.POST, evento=evento)
        if form.is_valid():
            inscricao = form.cleaned_data['inscricao']
            _, created = OperadorPresenca.objects.get_or_create(
                inscricao=inscricao,
                defaults={'designado_por': request.user},
            )
            nome = inscricao.usuario.get_full_name() or inscricao.usuario.username
            if created:
                messages.success(request, f'{nome} agora pode operar o leitor de presença.')
            else:
                messages.info(request, f'{nome} já é operador de presença.')
            return redirect('gerenciar_operadores', slug=slug)
    else:
        form = OperadorPresencaForm(evento=evento)

    operadores = (
        OperadorPresenca.objects.filter(inscricao__evento=evento)
        .select_related('inscricao__usuario', 'designado_por')
        .order_by('inscricao__usuario__first_name', 'inscricao__usuario__last_name')
    )

    return render(request, 'sessoes/operadores.html', {
        'evento': evento,
        'form': form,
        'operadores': operadores,
    })


@lideranca_required
def remover_operador(request, slug, operador_id):
    if request.method != 'POST':
        return redirect('gerenciar_operadores', slug=slug)

    evento = get_object_or_404(Evento, slug=slug)
    operador = get_object_or_404(
        OperadorPresenca, pk=operador_id, inscricao__evento=evento,
    )
    nome = operador.inscricao.usuario.get_full_name() or operador.inscricao.usuario.username
    operador.delete()
    messages.success(request, f'{nome} não é mais operador de presença.')
    return redirect('gerenciar_operadores', slug=slug)
