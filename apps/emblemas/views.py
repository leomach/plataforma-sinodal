from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Prefetch, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.emblemas.models import CatalogoEmblema, Emblema, EmblemaUsuario
from apps.emblemas.services import publicar_emblema
from apps.eventos.models import Evento, Inscricao
from apps.usuarios.models import User
from core import constants


def _is_lideranca(request):
    return request.user.is_superuser or request.user.tipo == constants.LIDERANCA


# ─── PAINEL ──────────────────────────────────────────────────────────────────

@login_required
def painel(request):
    if not _is_lideranca(request):
        return redirect('home')

    emblemas = (
        Emblema.objects.select_related('evento', 'criado_por')
        .annotate(total_destinatarios=Count('conquistas'))
        .order_by('-criado_em')
    )

    evento_slug = request.GET.get('evento', '').strip()
    status_filtro = request.GET.get('status', '').strip()

    if evento_slug == '__global__':
        emblemas = emblemas.filter(evento__isnull=True)
    elif evento_slug:
        emblemas = emblemas.filter(evento__slug=evento_slug)

    if status_filtro:
        try:
            emblemas = emblemas.filter(status=int(status_filtro))
        except ValueError:
            status_filtro = ''

    eventos_com_emblemas = (
        Evento.objects.filter(emblemas__isnull=False).distinct().order_by('-data_inicio')
    )
    total_rascunhos = Emblema.objects.filter(status=constants.EMBLEMA_RASCUNHO).count()

    ctx = {
        'emblemas': emblemas,
        'eventos_com_emblemas': eventos_com_emblemas,
        'evento_slug': evento_slug,
        'status_filtro': status_filtro,
        'total_rascunhos': total_rascunhos,
        'RASCUNHO': constants.EMBLEMA_RASCUNHO,
        'PUBLICADO': constants.EMBLEMA_PUBLICADO,
    }
    return render(request, 'emblemas/painel.html', ctx)


# ─── CRIAR / EDITAR EMBLEMA ──────────────────────────────────────────────────

@login_required
def criar_emblema(request):
    if not _is_lideranca(request):
        return redirect('home')

    template_id = request.GET.get('template')
    template = None
    if template_id:
        template = CatalogoEmblema.objects.filter(pk=template_id, ativo=True).first()

    if request.method == 'POST':
        nome      = request.POST.get('nome', '').strip()
        icone     = request.POST.get('icone', '').strip() or '🏅'
        descricao = request.POST.get('descricao', '').strip()
        categoria = request.POST.get('categoria', '').strip()
        evento_id = request.POST.get('evento') or None

        if not nome or not descricao or not categoria:
            messages.error(request, 'Nome, descrição e categoria são obrigatórios.')
        else:
            emblema = Emblema.objects.create(
                nome=nome,
                icone=icone,
                descricao=descricao,
                categoria=categoria,
                evento_id=evento_id,
                criado_por=request.user,
            )
            messages.success(request, f'Emblema "{nome}" criado. Agora selecione os destinatários.')
            return redirect('emblema_selecionar', emblema_id=emblema.pk)

    inicial = {
        'icone':     template.icone     if template else '🏅',
        'nome':      template.nome      if template else '',
        'descricao': template.descricao if template else '',
        'categoria': template.categoria if template else '',
    }
    ctx = {
        'categorias': constants.EMBLEMA_CATEGORIA_CHOICES,
        'eventos': Evento.objects.order_by('-data_inicio'),
        'catalogo': CatalogoEmblema.objects.filter(ativo=True).order_by('categoria', 'nome'),
        'inicial': inicial,
    }
    return render(request, 'emblemas/form.html', ctx)


@login_required
def editar_emblema(request, emblema_id):
    if not _is_lideranca(request):
        return redirect('home')

    emblema = get_object_or_404(Emblema, pk=emblema_id, status=constants.EMBLEMA_RASCUNHO)

    if request.method == 'POST':
        nome      = request.POST.get('nome', '').strip()
        icone     = request.POST.get('icone', '').strip() or '🏅'
        descricao = request.POST.get('descricao', '').strip()
        categoria = request.POST.get('categoria', '').strip()
        evento_id = request.POST.get('evento') or None

        if not nome or not descricao or not categoria:
            messages.error(request, 'Nome, descrição e categoria são obrigatórios.')
        else:
            emblema.nome      = nome
            emblema.icone     = icone
            emblema.descricao = descricao
            emblema.categoria = categoria
            emblema.evento_id = evento_id
            emblema.save(update_fields=['nome', 'icone', 'descricao', 'categoria', 'evento_id'])
            messages.success(request, 'Emblema atualizado.')
            return redirect('premiacoes_painel')

    ctx = {
        'emblema': emblema,
        'categorias': constants.EMBLEMA_CATEGORIA_CHOICES,
        'eventos': Evento.objects.order_by('-data_inicio'),
    }
    return render(request, 'emblemas/form.html', ctx)


@login_required
def excluir_emblema(request, emblema_id):
    if not _is_lideranca(request):
        return redirect('home')
    if request.method == 'POST':
        emblema = get_object_or_404(Emblema, pk=emblema_id, status=constants.EMBLEMA_RASCUNHO)
        nome = emblema.nome
        emblema.delete()
        messages.success(request, f'Emblema "{nome}" excluído.')
    return redirect('premiacoes_painel')


# ─── SELECIONAR DESTINATÁRIOS ────────────────────────────────────────────────

@login_required
def selecionar_destinatarios(request, emblema_id):
    if not _is_lideranca(request):
        return redirect('home')

    emblema = get_object_or_404(Emblema, pk=emblema_id, status=constants.EMBLEMA_RASCUNHO)

    q               = request.GET.get('q', '').strip()
    papel_filtro    = request.GET.get('papel', '').strip()
    apenas_presentes = request.GET.get('presentes', '') == '1'

    if emblema.evento_id:
        inscricoes = (
            Inscricao.objects.filter(
                evento=emblema.evento,
                status=constants.STATUS_APROVADO,
            ).select_related('usuario')
        )
        if papel_filtro:
            inscricoes = inscricoes.filter(papel_evento=papel_filtro)
        if apenas_presentes:
            inscricoes = inscricoes.filter(
                presencas__presente=True,
                presencas__sessao__evento=emblema.evento,
            ).distinct()
        if q:
            inscricoes = inscricoes.filter(
                Q(usuario__first_name__icontains=q) |
                Q(usuario__last_name__icontains=q)
            )
        inscricoes = inscricoes.order_by('usuario__first_name', 'usuario__last_name')
        participantes = [
            {'usuario': insc.usuario, 'papel': insc.get_papel_evento_display()}
            for insc in inscricoes
        ]
    else:
        qs = User.objects.filter(is_active=True)
        if q:
            qs = qs.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q))
        else:
            # Sem busca e sem evento: limita a 100 para não carregar toda a plataforma
            qs = qs.none() if not q else qs
        qs = qs.order_by('first_name', 'last_name')[:200]
        participantes = [{'usuario': u, 'papel': u.get_tipo_display()} for u in qs]

    requer_busca = not emblema.evento_id and not q

    ctx = {
        'emblema': emblema,
        'participantes': participantes,
        'q': q,
        'papel_filtro': papel_filtro,
        'apenas_presentes': apenas_presentes,
        'papeis': constants.PAPEL_EVENTO_CHOICES,
        'requer_busca': requer_busca,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'emblemas/partials/lista_usuarios.html', ctx)
    return render(request, 'emblemas/selecionar.html', ctx)


# ─── PUBLICAR ────────────────────────────────────────────────────────────────

@login_required
def publicar_emblema_view(request, emblema_id):
    if not _is_lideranca(request):
        return redirect('home')
    if request.method != 'POST':
        return redirect('premiacoes_painel')

    emblema = get_object_or_404(Emblema, pk=emblema_id, status=constants.EMBLEMA_RASCUNHO)
    ids_raw = request.POST.getlist('destinatarios')
    destinatarios_ids = [int(v) for v in ids_raw if v.isdigit()]

    if not destinatarios_ids:
        messages.error(request, 'Selecione ao menos um destinatário antes de publicar.')
        return redirect('emblema_selecionar', emblema_id=emblema_id)

    criados, ja_tinham = publicar_emblema(emblema, destinatarios_ids, request.user)

    msg = f'Emblema "{emblema.nome}" publicado para {criados} participante(s).'
    if ja_tinham:
        msg += f' {ja_tinham} já tinham esse emblema e foram ignorados.'
    messages.success(request, msg)
    return redirect('premiacoes_painel')




@login_required
def marcar_notificacao_lida(request, conquista_id):
    if request.method == 'POST':
        EmblemaUsuario.objects.filter(
            pk=conquista_id, usuario=request.user, notificado=False
        ).update(notificado=True)
    return HttpResponse(status=204)


# ─── CATÁLOGO ────────────────────────────────────────────────────────────────

@login_required
def catalogo(request):
    if not _is_lideranca(request):
        return redirect('home')
    templates = CatalogoEmblema.objects.all().order_by('categoria', 'nome')
    ctx = {
        'templates': templates,
        'categorias': constants.EMBLEMA_CATEGORIA_CHOICES,
    }
    return render(request, 'emblemas/catalogo.html', ctx)


@login_required
def catalogo_criar(request):
    if not _is_lideranca(request):
        return redirect('home')

    if request.method == 'POST':
        nome      = request.POST.get('nome', '').strip()
        icone     = request.POST.get('icone', '').strip() or '🏅'
        descricao = request.POST.get('descricao', '').strip()
        categoria = request.POST.get('categoria', '').strip()

        if not nome or not descricao or not categoria:
            messages.error(request, 'Nome, descrição e categoria são obrigatórios.')
        else:
            CatalogoEmblema.objects.create(
                nome=nome, icone=icone, descricao=descricao,
                categoria=categoria, criado_por=request.user,
            )
            messages.success(request, f'Template "{nome}" adicionado ao catálogo.')
            return redirect('emblema_catalogo')

    ctx = {'categorias': constants.EMBLEMA_CATEGORIA_CHOICES}
    return render(request, 'emblemas/catalogo_form.html', ctx)


@login_required
def catalogo_editar(request, template_id):
    if not _is_lideranca(request):
        return redirect('home')

    tmpl = get_object_or_404(CatalogoEmblema, pk=template_id)

    if request.method == 'POST':
        nome      = request.POST.get('nome', '').strip()
        icone     = request.POST.get('icone', '').strip() or '🏅'
        descricao = request.POST.get('descricao', '').strip()
        categoria = request.POST.get('categoria', '').strip()
        ativo     = request.POST.get('ativo') == '1'

        if not nome or not descricao or not categoria:
            messages.error(request, 'Nome, descrição e categoria são obrigatórios.')
        else:
            tmpl.nome      = nome
            tmpl.icone     = icone
            tmpl.descricao = descricao
            tmpl.categoria = categoria
            tmpl.ativo     = ativo
            tmpl.save(update_fields=['nome', 'icone', 'descricao', 'categoria', 'ativo'])
            messages.success(request, 'Template atualizado.')
            return redirect('emblema_catalogo')

    ctx = {
        'tmpl': tmpl,
        'categorias': constants.EMBLEMA_CATEGORIA_CHOICES,
    }
    return render(request, 'emblemas/catalogo_form.html', ctx)


@login_required
def catalogo_excluir(request, template_id):
    if not _is_lideranca(request):
        return redirect('home')
    if request.method == 'POST':
        tmpl = get_object_or_404(CatalogoEmblema, pk=template_id)
        tmpl.delete()
        messages.success(request, 'Template removido do catálogo.')
    return redirect('emblema_catalogo')
