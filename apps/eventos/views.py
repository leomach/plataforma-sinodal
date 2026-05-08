from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Evento, Inscricao, CampoEvento, RespostaInscricao, Sessao, Presenca
from .forms import InscricaoForm, EventoForm, CampoEventoFormSet
from core import constants

def is_lideranca(user):
    return user.is_superuser or user.tipo == constants.LIDERANCA

def lista_eventos(request):
    eventos_ativos = Evento.objects.filter(ativo=True).order_by('-data_inicio')
    return render(request, 'eventos/lista.html', {'eventos': eventos_ativos})

def detalhe_evento(request, slug):
    evento = get_object_or_404(Evento, slug=slug)
    inscricao = None
    if request.user.is_authenticated:
        inscricao = Inscricao.objects.filter(usuario=request.user, evento=evento).first()
    
    return render(request, 'eventos/detalhe.html', {
        'evento': evento,
        'inscricao': inscricao,
        'ja_inscrito': inscricao is not None
    })

@login_required
def inscrever_evento(request, slug):
    evento = get_object_or_404(Evento, slug=slug, ativo=True)
    
    if Inscricao.objects.filter(usuario=request.user, evento=evento).exists():
        messages.warning(request, 'Você já está inscrito neste evento.')
        return redirect('detalhe_evento', slug=slug)

    if request.method == 'POST':
        form = InscricaoForm(request.POST, evento=evento)
        if form.is_valid():
            inscricao = form.save(commit=False)
            inscricao.usuario = request.user
            inscricao.evento = evento
            inscricao.save()
            form.save_custom_fields(inscricao)
            messages.success(request, 'Inscrição realizada com sucesso! Aguarde a validação.')
            return redirect('detalhe_evento', slug=slug)
    else:
        form = InscricaoForm(evento=evento)

    return render(request, 'eventos/inscrever.html', {
        'evento': evento,
        'form': form
    })

@login_required
@user_passes_test(is_lideranca)
def gerenciar_eventos(request):
    eventos = Evento.objects.all().order_by('-data_inicio')
    return render(request, 'eventos/gerenciar.html', {'eventos': eventos})

@login_required
@user_passes_test(is_lideranca)
def criar_evento(request):
    if request.method == 'POST':
        form = EventoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Evento criado com sucesso!')
            return redirect('gerenciar_eventos')
    else:
        form = EventoForm()
    return render(request, 'eventos/form_evento.html', {'form': form, 'titulo': 'Novo Evento'})

@login_required
@user_passes_test(is_lideranca)
def editar_evento(request, slug):
    evento = get_object_or_404(Evento, slug=slug)
    if request.method == 'POST':
        form = EventoForm(request.POST, request.FILES, instance=evento)
        if form.is_valid():
            form.save()
            messages.success(request, 'Evento atualizado com sucesso!')
            return redirect('gerenciar_eventos')
    else:
        form = EventoForm(instance=evento)
    return render(request, 'eventos/form_evento.html', {'form': form, 'titulo': 'Editar Evento', 'evento': evento})

@login_required
@user_passes_test(is_lideranca)
def gerenciar_campos_evento(request, slug):
    evento = get_object_or_404(Evento, slug=slug)
    if request.method == 'POST':
        formset = CampoEventoFormSet(request.POST, instance=evento)
        if formset.is_valid():
            formset.save()
            messages.success(request, 'Formulário de inscrição atualizado com sucesso!')
            return redirect('gerenciar_eventos')
    else:
        formset = CampoEventoFormSet(instance=evento)
    
    return render(request, 'eventos/gerenciar_campos.html', {
        'evento': evento,
        'formset': formset
    })

@login_required
@user_passes_test(is_lideranca)
def gerenciar_inscricoes(request, slug):
    evento = get_object_or_404(Evento, slug=slug)
    status_filter = request.GET.get('status')
    inscricoes = Inscricao.objects.filter(evento=evento).order_by('-data_inscricao')
    
    if status_filter:
        inscricoes = inscricoes.filter(status=status_filter)
        
    return render(request, 'eventos/inscricoes.html', {
        'evento': evento,
        'inscricoes': inscricoes,
        'status_choices': constants.STATUS_INSCRICAO_CHOICES
    })

@login_required
@user_passes_test(is_lideranca)
def validar_inscricao(request, inscricao_id, acao):
    inscricao = get_object_or_404(Inscricao, id=inscricao_id)
    if acao == 'aprovar':
        inscricao.status = constants.STATUS_APROVADO
        messages.success(request, f'Inscrição de {inscricao.usuario.short_name} aprovada.')
    elif acao == 'rejeitar':
        inscricao.status = constants.STATUS_REJEITADO
        messages.warning(request, f'Inscrição de {inscricao.usuario.short_name} rejeitada.')
    
    inscricao.save()
    return redirect('gerenciar_inscricoes', slug=inscricao.evento.slug)

@login_required
def hub_evento(request, slug):
    evento = get_object_or_404(Evento, slug=slug)
    inscricao = get_object_or_404(Inscricao, usuario=request.user, evento=evento)
    
    if inscricao.status != constants.STATUS_APROVADO:
        messages.error(request, 'Você precisa ter sua inscrição aprovada para acessar o Hub.')
        return redirect('detalhe_evento', slug=slug)
    
    # Filtra documentos conforme o papel do usuário
    documentos = evento.documentos.all()
    if inscricao.papel_evento not in [constants.PAPEL_DELEGADO, constants.PAPEL_EX_OFFICIO]:
        documentos = documentos.filter(restrito_delegados=False)
        
    return render(request, 'eventos/hub.html', {
        'evento': evento,
        'inscricao': inscricao,
        'documentos': documentos
    })
