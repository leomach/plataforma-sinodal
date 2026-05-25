from apps.emblemas.models import EmblemaUsuario


def emblemas_pendentes(request):
    if not request.user.is_authenticated:
        return {}
    pendentes = list(
        EmblemaUsuario.objects.filter(usuario=request.user, notificado=False)
        .select_related('emblema__evento')
        .order_by('-concedido_em')[:5]
    )
    return {'emblemas_pendentes': pendentes}
