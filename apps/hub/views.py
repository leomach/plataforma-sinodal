from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.eventos.models import Evento, Inscricao
from core import constants
from functools import wraps

def inscricao_aprovada_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, slug, *args, **kwargs):
        evento = get_object_or_404(Evento, slug=slug)
        inscricao = Inscricao.objects.filter(usuario=request.user, evento=evento).first()
        
        if not inscricao or inscricao.status != constants.STATUS_APROVADO:
            messages.error(request, 'Você precisa ter sua inscrição aprovada para acessar o Hub.')
            return redirect('detalhe_evento', slug=slug)
        
        return view_func(request, evento, inscricao, *args, **kwargs)
    return login_required(_wrapped_view)

@inscricao_aprovada_required
def hub_evento(request, evento, inscricao):
    documentos = evento.documentos.all()
    if inscricao.papel_evento not in [constants.PAPEL_DELEGADO, constants.PAPEL_EX_OFFICIO]:
        documentos = documentos.filter(restrito_delegados=False)

    return render(request, 'hub/index.html', {
        'evento': evento,
        'inscricao': inscricao,
        'documentos': documentos,
    })
