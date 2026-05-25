import re

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404, render

from apps.emblemas.models import EmblemaUsuario
from apps.eventos.models import Evento, Inscricao
from apps.usuarios.models import User
from core import constants

_POR_PAGINA = 24


def _prefetch_emblemas():
    return Prefetch(
        'emblemas',
        queryset=EmblemaUsuario.objects.filter(
            emblema__status=constants.EMBLEMA_PUBLICADO
        ).select_related('emblema').order_by('-concedido_em'),
        to_attr='emblemas_publicados',
    )


def _qs_usuarios(evento_id, busca):
    if evento_id:
        qs = User.objects.filter(
            inscricoes__status=constants.STATUS_APROVADO,
            inscricoes__evento_id=evento_id,
        )
    else:
        qs = User.objects.filter(inscricoes__status=constants.STATUS_APROVADO)

    if busca:
        qs = qs.filter(Q(first_name__icontains=busca) | Q(last_name__icontains=busca))

    return (
        qs.distinct()
        .prefetch_related(_prefetch_emblemas())
        .order_by('first_name', 'last_name')
    )


@login_required
def explorar(request):
    meus_eventos = list(
        Evento.objects.filter(
            inscritos__usuario=request.user,
            inscritos__status=constants.STATUS_APROVADO,
        )
        .distinct()
        .order_by('-data_inicio')
    )

    evento_id = request.GET.get('evento', '').strip()
    busca = request.GET.get('q', '').strip()

    qs = _qs_usuarios(evento_id or None, busca or None)
    paginator = Paginator(qs, _POR_PAGINA)
    page_obj = paginator.get_page(request.GET.get('pagina', 1))

    ctx = {
        'page_obj': page_obj,
        'meus_eventos': meus_eventos,
        'evento_id': evento_id,
        'busca': busca,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'hub/partials/explorar_grid.html', ctx)
    return render(request, 'hub/explorar.html', ctx)


def _whatsapp_link(numero):
    digitos = re.sub(r'\D', '', numero or '')
    if not digitos:
        return ''
    if digitos.startswith('55') and len(digitos) >= 12:
        return f'https://wa.me/{digitos}'
    return f'https://wa.me/55{digitos}'


@login_required
def perfil_usuario(request, user_id):
    usuario = get_object_or_404(
        User.objects.prefetch_related(
            Prefetch(
                'inscricoes',
                queryset=Inscricao.objects.filter(
                    status=constants.STATUS_APROVADO
                ).select_related('evento').order_by('-evento__data_inicio'),
                to_attr='inscricoes_aprovadas',
            ),
            Prefetch(
                'emblemas',
                queryset=EmblemaUsuario.objects.filter(
                    emblema__status=constants.EMBLEMA_PUBLICADO
                ).select_related('emblema__evento').order_by('-concedido_em'),
                to_attr='emblemas_publicados',
            ),
        ),
        pk=user_id,
    )
    return render(request, 'hub/partials/perfil_usuario.html', {
        'perfil': usuario,
        'whatsapp_link': _whatsapp_link(usuario.whatsapp),
    })
