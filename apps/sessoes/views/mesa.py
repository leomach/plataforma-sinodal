import json as _json

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.eventos.models import Evento, Inscricao
from apps.sessoes.forms import MesaDiretoraForm, TransferirPresidenciaForm
from apps.sessoes.models import MembroDaMesa, Sessao
from apps.sessoes.services import eventlog as log_service
from apps.sessoes.views.painel import lideranca_required
from core import constants

_CARGO_TO_FIELD = {
    MembroDaMesa.PRESIDENTE: 'presidente',
    MembroDaMesa.VICE_PRESIDENTE: 'vice_presidente',
    MembroDaMesa.PRIMEIRO_SECRETARIO: 'primeiro_secretario',
    MembroDaMesa.SEGUNDO_SECRETARIO: 'segundo_secretario',
    MembroDaMesa.TESOUREIRO: 'tesoureiro',
    MembroDaMesa.SECRETARIO_EXECUTIVO: 'secretario_executivo',
}

_CAMPO_CARGO = [
    ('presidente', MembroDaMesa.PRESIDENTE),
    ('vice_presidente', MembroDaMesa.VICE_PRESIDENTE),
    ('primeiro_secretario', MembroDaMesa.PRIMEIRO_SECRETARIO),
    ('segundo_secretario', MembroDaMesa.SEGUNDO_SECRETARIO),
    ('tesoureiro', MembroDaMesa.TESOUREIRO),
    ('secretario_executivo', MembroDaMesa.SECRETARIO_EXECUTIVO),
]


def _inscricoes_para_js(evento):
    qs = Inscricao.objects.filter(
        evento=evento,
        status=constants.STATUS_APROVADO,
    ).select_related('usuario').order_by('usuario__first_name', 'usuario__last_name')
    return [
        {'id': i.pk, 'nome': i.usuario.get_full_name() or i.usuario.username}
        for i in qs
    ]


def _parse_extras(raw, evento):
    try:
        itens = _json.loads(raw or '[]')
    except (ValueError, TypeError):
        return []

    if not itens:
        return []

    # Coleta IDs e cargos sem queries
    id_to_cargo = {}
    order = []
    for item in itens:
        try:
            insc_id = int(item.get('inscricao_id', 0))
            cargo_desc = str(item.get('cargo_descricao', '')).strip()
            if insc_id and cargo_desc:
                id_to_cargo[insc_id] = cargo_desc
                order.append(insc_id)
        except (ValueError, TypeError):
            continue

    if not id_to_cargo:
        return []

    # Uma única query em lote em vez de uma query por item
    inscricoes = {
        i.pk: i
        for i in Inscricao.objects.filter(
            pk__in=id_to_cargo.keys(),
            evento=evento,
            status=constants.STATUS_APROVADO,
        ).select_related('usuario')
    }

    return [
        {
            'inscricao_id': insc_id,
            'nome': inscricoes[insc_id].usuario.get_full_name() or inscricoes[insc_id].usuario.username,
            'cargo_descricao': id_to_cargo[insc_id],
        }
        for insc_id in order
        if insc_id in inscricoes
    ]


@lideranca_required
def compor_mesa(request, slug, sessao_id):
    evento = get_object_or_404(Evento, slug=slug)
    sessao = get_object_or_404(Sessao, pk=sessao_id, evento=evento)

    tem_mesa_atual = sessao.membros_mesa.filter(encerrou_em__isnull=True).exists()
    sessao_anterior = None
    if not tem_mesa_atual:
        sessao_anterior = (
            Sessao.objects.filter(evento=evento)
            .exclude(pk=sessao_id)
            .order_by('-data_hora')
            .first()
        )

    if request.method == 'POST':
        form = MesaDiretoraForm(request.POST, evento=evento)
        if form.is_valid():
            now = timezone.now()
            sessao.membros_mesa.filter(encerrou_em__isnull=True).update(encerrou_em=now)

            novos_membros = []
            for fname, cargo in _CAMPO_CARGO:
                inscricao = form.cleaned_data.get(fname)
                if inscricao:
                    m = MembroDaMesa.objects.create(sessao=sessao, inscricao=inscricao, cargo=cargo)
                    novos_membros.append(m)

            membros_extras = _parse_extras(
                form.cleaned_data.get('membros_extras_json'), evento
            )
            sessao.membros_extras = membros_extras
            sessao.save(update_fields=['membros_extras'])

            if novos_membros or membros_extras:
                log_service.log_mesa_composta(sessao, novos_membros, membros_extras)
            messages.success(request, 'Mesa Diretora definida com sucesso.')
            return redirect('painel_sessao', slug=slug, sessao_id=sessao_id)
    else:
        initial = {}
        membros_atuais = sessao.membros_mesa.filter(encerrou_em__isnull=True).select_related('inscricao')
        if membros_atuais.exists():
            for m in membros_atuais:
                fname = _CARGO_TO_FIELD.get(m.cargo)
                if fname:
                    initial[fname] = m.inscricao
            initial['membros_extras_json'] = _json.dumps(sessao.membros_extras or [])
        elif sessao_anterior:
            # Uma query ordenada por cargo e data — substitui 6 queries em loop
            vistos = set()
            membros_ant = (
                sessao_anterior.membros_mesa
                .select_related('inscricao')
                .order_by('cargo', '-assumiu_em')
            )
            for m in membros_ant:
                if m.cargo not in vistos:
                    vistos.add(m.cargo)
                    fname = _CARGO_TO_FIELD.get(m.cargo)
                    if fname:
                        initial[fname] = m.inscricao
            initial['membros_extras_json'] = _json.dumps(sessao_anterior.membros_extras or [])

        form = MesaDiretoraForm(initial=initial, evento=evento)

    return render(request, 'sessoes/mesa.html', {
        'evento': evento,
        'sessao': sessao,
        'form': form,
        'sessao_anterior': sessao_anterior if not tem_mesa_atual else None,
        'inscricoes_para_js': _inscricoes_para_js(evento),
    })


@lideranca_required
def transferir_presidencia(request, slug, sessao_id):
    if request.method != 'POST':
        return redirect('painel_sessao', slug=slug, sessao_id=sessao_id)

    evento = get_object_or_404(Evento, slug=slug)
    sessao = get_object_or_404(Sessao, pk=sessao_id, evento=evento)

    presidente_atual = sessao.membros_mesa.filter(
        cargo=MembroDaMesa.PRESIDENTE,
        encerrou_em__isnull=True,
    ).select_related('inscricao__usuario').first()

    if not presidente_atual:
        messages.error(request, 'Não há presidente ativo na mesa.')
        return redirect('painel_sessao', slug=slug, sessao_id=sessao_id)

    form = TransferirPresidenciaForm(request.POST, sessao=sessao)
    if form.is_valid():
        membro_selecionado = form.cleaned_data['novo_presidente']
        now = timezone.now()

        presidente_atual.encerrou_em = now
        presidente_atual.save(update_fields=['encerrou_em'])

        cargo_anterior_selecionado = membro_selecionado.cargo
        membro_selecionado.encerrou_em = now
        membro_selecionado.save(update_fields=['encerrou_em'])

        MembroDaMesa.objects.create(
            sessao=sessao,
            inscricao=membro_selecionado.inscricao,
            cargo=MembroDaMesa.PRESIDENTE,
        )
        MembroDaMesa.objects.create(
            sessao=sessao,
            inscricao=presidente_atual.inscricao,
            cargo=cargo_anterior_selecionado,
        )

        log_service.log_transferencia_presidencia(
            sessao=sessao,
            de_membro=presidente_atual,
            para_membro=membro_selecionado,
            cargo_novo_do_ex_presidente=cargo_anterior_selecionado,
            usuario=request.user,
        )
        nome = membro_selecionado.inscricao.usuario.get_full_name() or membro_selecionado.inscricao.usuario.username
        messages.success(request, f'Presidência transferida para {nome}.')
    else:
        messages.error(request, 'Selecione um membro válido da mesa.')

    return redirect('painel_sessao', slug=slug, sessao_id=sessao_id)
