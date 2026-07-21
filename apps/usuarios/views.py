from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from .forms import CustomUserCreationForm, ProfileUpdateForm, LiderancaUserEditForm
from .models import User
from core import constants
from apps.eventos.models import Inscricao, Evento

def _superusuarios_contato():
    import re
    admins = User.objects.filter(is_superuser=True).exclude(whatsapp='').order_by('first_name')
    return [
        {
            'first_name': a.first_name,
            'last_name': a.last_name,
            'whatsapp': a.whatsapp,
            'whatsapp_digitos': re.sub(r'\D', '', a.whatsapp),
        }
        for a in admins
    ]


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()

    # Detecta se algum dos erros é de duplicidade para exibir contatos
    duplicate_codes = {'duplicate_email', 'duplicate_whatsapp'}
    tem_duplicata = any(
        any(e.code in duplicate_codes for e in field_errors)
        for field_errors in form.errors.as_data().values()
    )

    return render(request, 'usuarios/register.html', {
        'form': form,
        'tem_duplicata': tem_duplicata,
        'admins_contato': _superusuarios_contato() if tem_duplicata else [],
    })

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
            Q(username__unaccent__icontains=query) |
            Q(first_name__unaccent__icontains=query) |
            Q(last_name__unaccent__icontains=query) |
            Q(email__unaccent__icontains=query)
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
    from apps.emblemas.models import EmblemaUsuario
    inscricoes = Inscricao.objects.filter(usuario=request.user).order_by('-data_inscricao')
    meus_emblemas = (
        EmblemaUsuario.objects.filter(usuario=request.user)
        .select_related('emblema__evento')
        .order_by('-concedido_em')
    )

    form = ProfileUpdateForm(instance=request.user)
    password_form = PasswordChangeForm(request.user)
    active_tab = 'dados'

    if request.method == 'POST':
        if request.POST.get('form_type') == 'senha':
            active_tab = 'seguranca'
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                # Mantém a sessão ativa após trocar a senha
                update_session_auth_hash(request, user)
                messages.success(request, 'Senha alterada com sucesso.')
                return redirect('perfil')
            messages.error(request, 'Não foi possível alterar a senha. Verifique os campos abaixo.')
        else:
            form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Perfil atualizado com sucesso.')
                return redirect('perfil')

    return render(request, 'usuarios/perfil.html', {
        'form': form,
        'password_form': password_form,
        'active_tab': active_tab,
        'inscricoes': inscricoes,
        'meus_emblemas': meus_emblemas,
    })


@login_required
@user_passes_test(is_lideranca)
def detalhes_usuario(request, user_id):
    from apps.emblemas.models import EmblemaUsuario
    usuario = get_object_or_404(User, id=user_id)
    inscricoes = (
        Inscricao.objects.filter(usuario=usuario)
        .select_related('evento')
        .order_by('-data_inscricao')
    )
    emblemas = (
        EmblemaUsuario.objects.filter(usuario=usuario)
        .select_related('emblema__evento')
        .order_by('-concedido_em')
    )
    return render(request, 'usuarios/detalhes_usuario.html', {
        'usuario': usuario,
        'inscricoes': inscricoes,
        'emblemas': emblemas,
    })


@login_required
@user_passes_test(is_lideranca)
def editar_usuario(request, user_id):
    usuario = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = LiderancaUserEditForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, f'Dados de {usuario.display_name} atualizados com sucesso.')
            return redirect('detalhes_usuario', user_id=usuario.id)
    else:
        form = LiderancaUserEditForm(instance=usuario)
    return render(request, 'usuarios/editar_usuario.html', {
        'form': form,
        'usuario': usuario,
    })


@login_required
@user_passes_test(is_lideranca)
def resetar_senha_usuario(request, user_id):
    usuario = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        if usuario.is_superuser:
            messages.error(request, 'Não é possível resetar a senha de um superusuário por aqui.')
        else:
            # A nova senha passa a ser o próprio nome de usuário.
            usuario.set_password(usuario.username)
            usuario.save()
            messages.success(
                request,
                f'Senha de {usuario.display_name} redefinida. '
                f'Agora ele pode entrar usando o nome de usuário (@{usuario.username}) como senha.'
            )
    return redirect(request.POST.get('next') or 'gerenciar_usuarios')


@login_required
@user_passes_test(is_lideranca)
def toggle_ativo_usuario(request, user_id):
    usuario = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        if usuario == request.user:
            messages.error(request, 'Você não pode desativar a própria conta.')
        elif usuario.is_superuser:
            messages.error(request, 'Não é possível desativar um superusuário.')
        else:
            usuario.is_active = not usuario.is_active
            usuario.save(update_fields=['is_active'])
            estado = 'ativado' if usuario.is_active else 'desativado'
            messages.success(request, f'Acesso de {usuario.display_name} {estado}.')
    return redirect(request.POST.get('next') or 'gerenciar_usuarios')
