from django.utils import timezone

from apps.emblemas.models import Emblema, EmblemaUsuario
from core import constants


def publicar_emblema(emblema, destinatarios_ids, concedido_por):
    """
    Publica um Emblema em rascunho para os user IDs recebidos.
    Retorna (criados, ja_tinham).
    """
    ja_tinham = set(
        EmblemaUsuario.objects.filter(
            emblema=emblema, usuario_id__in=destinatarios_ids
        ).values_list('usuario_id', flat=True)
    )

    novos = [
        EmblemaUsuario(
            emblema=emblema,
            usuario_id=uid,
            concedido_por=concedido_por,
        )
        for uid in destinatarios_ids
        if uid not in ja_tinham
    ]
    EmblemaUsuario.objects.bulk_create(novos)

    emblema.status = constants.EMBLEMA_PUBLICADO
    emblema.publicado_em = timezone.now()
    emblema.save(update_fields=['status', 'publicado_em'])

    return len(novos), len(ja_tinham)


def publicar_todos_rascunhos(concedido_por, evento=None):
    """
    Publica todos os Emblemas em rascunho.
    evento=None → publica rascunhos globais (sem evento).
    evento=<obj> → publica rascunhos daquele evento.
    Retorna total de EmblemaUsuario criados.
    """
    qs = Emblema.objects.filter(status=constants.EMBLEMA_RASCUNHO)
    if evento is not None:
        qs = qs.filter(evento=evento)
    else:
        qs = qs.filter(evento__isnull=True)

    total = 0
    for emblema in qs:
        ids = list(emblema.conquistas.values_list('usuario_id', flat=True))
        criados, _ = publicar_emblema(emblema, ids, concedido_por)
        total += criados
    return total
