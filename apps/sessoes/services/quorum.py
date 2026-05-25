from core import constants


def calcular_delegacao_esperada(evento_id: int) -> int:
    from apps.eventos.models import Inscricao
    return Inscricao.objects.filter(
        evento_id=evento_id,
        status=constants.STATUS_APROVADO,
        papel_evento__in=[constants.PAPEL_DELEGADO, constants.PAPEL_EX_OFFICIO],
    ).count()


def calcular_presentes(sessao_id: int) -> int:
    from apps.sessoes.models import Presenca
    return Presenca.objects.filter(sessao_id=sessao_id, presente=True).count()


def quorum_atingido(sessao_id: int, evento_id: int = None) -> bool:
    return info_quorum(sessao_id, evento_id=evento_id)['atingido']


def info_quorum(sessao_id: int, evento_id: int = None) -> dict:
    """
    Retorna dados de quórum da sessão.
    Passar evento_id evita uma query extra para buscar a sessão.
    """
    if evento_id is None:
        from apps.sessoes.models import Sessao
        evento_id = Sessao.objects.values_list('evento_id', flat=True).get(pk=sessao_id)

    esperados = calcular_delegacao_esperada(evento_id)
    presentes = calcular_presentes(sessao_id)
    atingido = (presentes > esperados / 2) if esperados > 0 else False
    percentual = round((presentes / esperados * 100) if esperados > 0 else 0, 1)
    return {
        'presentes': presentes,
        'esperados': esperados,
        'atingido': atingido,
        'percentual': percentual,
    }


def calcular_info_quorum_delta(info_antes: dict, delta: int) -> dict:
    """
    Calcula novo info_quorum a partir de um delta (+1 entrada, -1 saída)
    sem tocar o banco — evita a terceira query em toggle_presenca.
    """
    presentes = max(0, info_antes['presentes'] + delta)
    esperados = info_antes['esperados']
    atingido = (presentes > esperados / 2) if esperados > 0 else False
    percentual = round((presentes / esperados * 100) if esperados > 0 else 0, 1)
    return {
        'presentes': presentes,
        'esperados': esperados,
        'atingido': atingido,
        'percentual': percentual,
    }
