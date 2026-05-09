from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.utils import timezone
from .forms import CustomUserCreationForm, ProfileUpdateForm
from .models import User
from core import constants
from apps.eventos.models import Inscricao, Evento

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'usuarios/register.html', {'form': form})

@login_required
def home(request):
    # Busca os próximos 3 eventos ativos que ainda não terminaram
    proximos_eventos = Evento.objects.filter(
        ativo=True, 
        data_fim__gte=timezone.now()
    ).order_by('data_inicio')[:3]
    
    return render(request, 'home.html', {
        'proximos_eventos': proximos_eventos
    })

def is_lideranca(user):
    return user.is_superuser or user.tipo == constants.LIDERANCA

@login_required
@user_passes_test(is_lideranca)
def gerenciar_usuarios(request):
    query = request.GET.get('q', '')
    usuarios = User.objects.all().order_by('username')
    
    if query:
        usuarios = usuarios.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )
        
    return render(request, 'usuarios/gerenciar.html', {
        'usuarios': usuarios,
        'query': query
    })

@login_required
@user_passes_test(is_lideranca)
def promover_usuario(request, user_id):
    usuario = get_object_or_404(User, id=user_id)
    if usuario.tipo == constants.SOCIO:
        usuario.tipo = constants.LIDERANCA
        usuario.save()
    return redirect('gerenciar_usuarios')

@login_required
@user_passes_test(is_lideranca)
def rebaixar_usuario(request, user_id):
    usuario = get_object_or_404(User, id=user_id)
    if usuario.tipo == constants.LIDERANCA and not usuario.is_superuser:
        usuario.tipo = constants.SOCIO
        usuario.save()
    return redirect('gerenciar_usuarios')

@login_required
def perfil(request):
    inscricoes = Inscricao.objects.filter(usuario=request.user).order_by('-data_inscricao')
    
    if request.method == 'POST':
        print("FILES received:", request.FILES)
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            print("Form is valid. Saving...")
            form.save()
            return redirect('perfil')
        else:
            print("Form errors:", form.errors)
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    return render(request, 'usuarios/perfil.html', {
        'form': form,
        'inscricoes': inscricoes
    })
