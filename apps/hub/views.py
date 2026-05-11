from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from apps.eventos.models import Evento, Inscricao
from .models import TipoDocumento, DocumentoEvento, Sessao
from .forms import DocumentoEventoForm, AtaSessaoRapidaForm
from core import constants
from functools import wraps

def is_lideranca(user):
    return user.is_superuser or user.tipo == constants.LIDERANCA

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
    # RBAC: Delegados e Ex-Officio podem ver tudo. Outros não vêem documentos restritos.
    is_delegado = inscricao.papel_evento in [constants.PAPEL_DELEGADO, constants.PAPEL_EX_OFFICIO]
    
    documentos_base = evento.documentos.all().select_related('tipo')
    if not is_delegado:
        documentos_base = documentos_base.filter(restrito_delegados=False)

    # Separa Atas de Sessão (Destaque)
    atas_atuais = documentos_base.filter(is_ata_sessao=True)
    
    # Agrupa por TipoDocumento para o Acervo
    tipos_com_documentos = []
    tipos = TipoDocumento.objects.all()
    
    for tipo in tipos:
        docs = documentos_base.filter(tipo=tipo, is_ata_sessao=False)
        if docs.exists():
            tipos_com_documentos.append({
                'tipo': tipo,
                'documentos': docs
            })

    # Agenda de Sessões
    sessoes = evento.sessoes.all().order_by('data_hora')

    return render(request, 'hub/index.html', {
        'evento': evento,
        'inscricao': inscricao,
        'atas_atuais': atas_atuais,
        'tipos_com_documentos': tipos_com_documentos,
        'sessoes': sessoes,
        'is_delegado': is_delegado,
        'is_lideranca': is_lideranca(request.user),
    })

@login_required
@user_passes_test(is_lideranca)
def gerenciar_documentos(request, slug):
    evento = get_object_or_404(Evento, slug=slug)
    documentos = evento.documentos.all().select_related('tipo')
    
    if request.method == 'POST':
        form = DocumentoEventoForm(request.POST)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.evento = evento
            doc.save()
            messages.success(request, 'Documento adicionado com sucesso!')
            return redirect('gerenciar_documentos_hub', slug=slug)
    else:
        form = DocumentoEventoForm()

    ata_form = AtaSessaoRapidaForm()
    
    return render(request, 'hub/gerenciar_documentos.html', {
        'evento': evento,
        'documentos': documentos,
        'form': form,
        'ata_form': ata_form,
    })

@login_required
@user_passes_test(is_lideranca)
def excluir_documento(request, pk):
    doc = get_object_or_404(DocumentoEvento, pk=pk)
    slug = doc.evento.slug
    doc.delete()
    messages.success(request, 'Documento excluído com sucesso!')
    return redirect('gerenciar_documentos_hub', slug=slug)

@login_required
@user_passes_test(is_lideranca)
def lancar_ata_rapida(request, slug):
    evento = get_object_or_404(Evento, slug=slug)
    if request.method == 'POST':
        form = AtaSessaoRapidaForm(request.POST)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.evento = evento
            doc.save()
            messages.success(request, 'Ata da sessão lançada com sucesso!')
    return redirect('gerenciar_documentos_hub', slug=slug)
