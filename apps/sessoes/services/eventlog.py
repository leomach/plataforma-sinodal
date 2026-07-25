from django.utils import timezone

from apps.sessoes.services import quorum as quorum_service


def _hora_agora() -> str:
    return timezone.localtime(timezone.now()).strftime('%H:%M')


def _plural(n: int, singular: str, plural_form: str) -> str:
    return f'{n} {singular}' if n == 1 else f'{n} {plural_form}'


def _criar_log(sessao, descricao, usuario=None):
    from apps.sessoes.models import EventoLog
    return EventoLog.objects.create(
        sessao=sessao,
        tipo=EventoLog.TIPO_AUTO,
        descricao=descricao,
        usuario=usuario,
    )


def log_sessao_aberta(sessao) -> 'EventoLog':
    from apps.sessoes.models import Presenca
    hora = _hora_agora()
    info = quorum_service.info_quorum(sessao.pk)
    status_q = (
        'sendo declarado atingido o quórum regimental'
        if info['atingido']
        else 'não sendo atingido o quórum regimental mínimo'
    )

    presencas = (
        Presenca.objects.filter(sessao=sessao, presente=True)
        .select_related('inscricao__usuario')
        .order_by('inscricao__usuario__first_name', 'inscricao__usuario__last_name')
    )
    nomes = [
        p.inscricao.usuario.get_full_name() or p.inscricao.usuario.username
        for p in presencas
    ]
    lista_nomes = (
        (': ' + ', '.join(nomes) + '.')
        if nomes
        else '.'
    )

    descricao = (
        f"Às {hora}, o Presidente declara aberta a sessão. "
        f"Encontram-se presentes {info['presentes']} delegados credenciados, {status_q}. "
        f"Registram presença{lista_nomes}"
    )
    return _criar_log(sessao, descricao)


def log_sessao_encerrada(sessao) -> 'EventoLog':
    hora = _hora_agora()
    return _criar_log(
        sessao,
        f'Nada mais havendo a tratar, o Presidente declara encerrada a sessão às {hora}.',
    )


def log_chamada_iniciada(sessao) -> 'EventoLog':
    return _criar_log(sessao, 'Procede-se à chamada nominal dos delegados credenciados.')


def log_chamada_cancelada(sessao) -> 'EventoLog':
    return _criar_log(sessao, 'A chamada de presença é interrompida e a sessão suspensa.')


def log_quorum_atingido(sessao) -> 'EventoLog':
    info = quorum_service.info_quorum(sessao.pk)
    descricao = (
        f"Declara-se atingido o quórum regimental, com {info['presentes']} delegados presentes "
        f"de um total de {info['esperados']} credenciados."
    )
    return _criar_log(sessao, descricao)


def log_entrada(sessao, inscricao) -> 'EventoLog':
    hora = _hora_agora()
    nome = inscricao.usuario.get_full_name() or inscricao.usuario.username
    return _criar_log(
        sessao,
        f'Às {hora}, o(a) delegado(a) {nome} ingressa no recinto do plenário.',
    )


def log_saida(sessao, inscricao) -> 'EventoLog':
    hora = _hora_agora()
    nome = inscricao.usuario.get_full_name() or inscricao.usuario.username
    return _criar_log(
        sessao,
        f'Às {hora}, o(a) delegado(a) {nome} retira-se do recinto do plenário, com anuência da presidência.',
    )


def log_presencas_importadas(sessao, quantidade: int, origem_nome: str) -> 'EventoLog':
    corpo = _plural(quantidade, 'participante', 'participantes')
    return _criar_log(
        sessao,
        f'Importada a lista de presença da sessão "{origem_nome}": '
        f'{corpo} registrado(s) como presente(s).',
    )


def log_votacao_aberta(votacao) -> 'EventoLog':
    return _criar_log(
        votacao.sessao,
        f'Submete-se ao plenário a seguinte proposta: "{votacao.titulo}".',
    )


def log_votacao_encerrada(votacao) -> 'EventoLog':
    from apps.sessoes.models import Votacao
    c = votacao.contagem()
    resultado = 'aprovar' if votacao.resultado == Votacao.RESULTADO_APROVADA else 'rejeitar'
    descricao = (
        f'Encerrada a votação da proposta "{votacao.titulo}", apura-se: '
        f'{_plural(c["favor"], "voto a favor", "votos a favor")}, '
        f'{_plural(c["contra"], "voto contra", "votos contra")} e '
        f'{_plural(c["abstencoes"], "abstenção", "abstenções")}. '
        f'O plenário resolve {resultado} a matéria.'
    )
    return _criar_log(votacao.sessao, descricao)


def log_voto_minerva(votacao) -> 'EventoLog':
    from apps.sessoes.models import Votacao
    voto = 'a favor' if votacao.voto_minerva_favor else 'contra'
    resultado = 'aprovar' if votacao.resultado == Votacao.RESULTADO_APROVADA else 'rejeitar'
    nome = votacao.minerva_por.get_full_name() if votacao.minerva_por else 'a liderança'
    descricao = (
        f'Verificado empate na votação, o Presidente {nome} exerce o Voto de Qualidade '
        f'(Voto de Minerva), manifestando-se {voto} a proposta. '
        f'Em consequência, o plenário resolve {resultado} a matéria em votação.'
    )
    return _criar_log(votacao.sessao, descricao, usuario=votacao.minerva_por)


def log_mesa_composta(sessao, membros: list, membros_extras: list = None) -> 'EventoLog':
    partes = []
    for m in membros:
        nome = m.inscricao.usuario.get_full_name() or m.inscricao.usuario.username
        partes.append(f'{m.cargo_label}: {nome}')
    for e in (membros_extras or []):
        partes.append(f'{e["cargo_descricao"]}: {e["nome"]}')
    if partes:
        composicao = '; '.join(partes)
        descricao = (
            f'Procede-se à composição da Mesa Diretora, ficando assim constituída: {composicao}.'
        )
    else:
        descricao = 'Mesa Diretora definida.'
    return _criar_log(sessao, descricao)


def log_transferencia_presidencia(sessao, de_membro, para_membro, cargo_novo_do_ex_presidente, usuario) -> 'EventoLog':
    from apps.sessoes.models import MembroDaMesa
    de_nome = de_membro.inscricao.usuario.get_full_name() or de_membro.inscricao.usuario.username
    para_nome = para_membro.inscricao.usuario.get_full_name() or para_membro.inscricao.usuario.username
    cargo_anterior = para_membro.cargo_label
    cargo_novo_label = dict(MembroDaMesa.CARGO_CHOICES).get(cargo_novo_do_ex_presidente, '')
    descricao = (
        f'O Presidente {de_nome} transfere a condução dos trabalhos ao {cargo_anterior} {para_nome}, que assume a presidência da sessão. '
        f'{de_nome} passa a ocupar o cargo de {cargo_novo_label}.'
    )
    return _criar_log(sessao, descricao, usuario=usuario)


def log_manual(sessao, descricao: str, usuario) -> 'EventoLog':
    from apps.sessoes.models import EventoLog
    return EventoLog.objects.create(
        sessao=sessao,
        tipo=EventoLog.TIPO_MANUAL,
        descricao=descricao,
        usuario=usuario,
    )
