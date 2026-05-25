from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.eventos.models import Evento
from apps.sessoes.forms import EventoLogManualForm
from apps.sessoes.models import EventoLog, Sessao
from apps.sessoes.services import eventlog as log_service
from apps.sessoes.views.painel import lideranca_required


@require_POST
@lideranca_required
def adicionar_log_manual(request, slug, sessao_id):
    evento = get_object_or_404(Evento, slug=slug)
    sessao = get_object_or_404(Sessao, pk=sessao_id, evento=evento)
    form = EventoLogManualForm(request.POST)
    if form.is_valid():
        log_service.log_manual(sessao, form.cleaned_data['descricao'], request.user)
        messages.success(request, 'Registro adicionado à linha do tempo.')
    else:
        messages.error(request, 'Descrição inválida.')
    return redirect('painel_sessao', slug=slug, sessao_id=sessao_id)


@lideranca_required
def exportar_log(request, slug, sessao_id):
    evento = get_object_or_404(Evento, slug=slug)
    sessao = get_object_or_404(Sessao, pk=sessao_id, evento=evento)
    logs = list(sessao.logs.select_related('usuario').order_by('timestamp'))

    agora = timezone.localtime(timezone.now()).strftime('%d/%m/%Y às %H:%M')
    data_sessao = timezone.localtime(sessao.data_hora).strftime('%d/%m/%Y')

    # A — Rascunho do corpo da ata: parágrafo único, sem horários
    rascunho_ata = ' '.join(log.descricao for log in logs) if logs else '(Sem registros.)'

    # B — Notas de rodapé sugeridas: apenas logs automáticos, numerados
    notas = []
    n = 1
    for log in logs:
        if log.tipo == EventoLog.TIPO_AUTO:
            hora = timezone.localtime(log.timestamp).strftime('%H:%M')
            resumo = log.descricao[:72] + ('…' if len(log.descricao) > 72 else '')
            notas.append(f'{n}. [{hora}] {resumo}')
            n += 1
    notas_rodape = '\n'.join(notas) if notas else '(Nenhum evento automático registrado.)'

    # C — Linha do tempo operacional: uso interno, com horário e tipo
    linha_tempo_linhas = []
    for log in logs:
        hora = timezone.localtime(log.timestamp).strftime('%H:%M')
        tipo = 'AUTO  ' if log.tipo == EventoLog.TIPO_AUTO else 'MANUAL'
        linha_tempo_linhas.append(f'[{hora}] [{tipo}] {log.descricao}')
    linha_tempo = '\n'.join(linha_tempo_linhas) if linha_tempo_linhas else '(Sem registros.)'

    # Conteúdo completo para download .txt
    sep = '=' * 64
    conteudo_download = '\n'.join([
        f'ATA — {sessao.nome.upper()}',
        f'Evento: {evento.titulo}',
        f'Data: {data_sessao}',
        sep,
        '',
        'A — RASCUNHO DO CORPO DA ATA',
        '(Parágrafo único. Cole diretamente no documento oficial.)',
        '',
        rascunho_ata,
        '',
        sep,
        '',
        'B — NOTAS DE RODAPÉ SUGERIDAS',
        '(Índice numerado para o rodapé da ata digital — fonte 10 na impressão.)',
        '',
        notas_rodape,
        '',
        sep,
        '',
        'C — LINHA DO TEMPO OPERACIONAL',
        '(Uso interno. Inclui horários e tipo AUTO/MANUAL.)',
        '',
        linha_tempo,
        '',
        sep,
        f'Gerado pela Plataforma Sinodal em {agora}.',
    ])

    if request.headers.get('HX-Request') or request.GET.get('modal'):
        return render(request, 'sessoes/exportar_log.html', {
            'evento': evento,
            'sessao': sessao,
            'rascunho_ata': rascunho_ata,
            'notas_rodape': notas_rodape,
            'linha_tempo': linha_tempo,
        })

    response = HttpResponse(conteudo_download, content_type='text/plain; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="ata-{sessao.pk}.txt"'
    return response


@require_POST
@lideranca_required
def excluir_log_manual(request, slug, sessao_id, log_id):
    evento = get_object_or_404(Evento, slug=slug)
    sessao = get_object_or_404(Sessao, pk=sessao_id, evento=evento)
    log = get_object_or_404(EventoLog, pk=log_id, sessao=sessao, tipo=EventoLog.TIPO_MANUAL)
    log.delete()
    messages.success(request, 'Registro removido da linha do tempo.')
    return redirect('painel_sessao', slug=slug, sessao_id=sessao_id)
