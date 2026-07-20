from django.urls import path
from django.contrib.auth import views as auth_views
from . import views, views_explorar

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='usuarios/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('perfil/', views.perfil, name='perfil'),
    path('gerenciar/', views.gerenciar_usuarios, name='gerenciar_usuarios'),
    path('gerenciar/<int:user_id>/', views.detalhes_usuario, name='detalhes_usuario'),
    path('gerenciar/<int:user_id>/editar/', views.editar_usuario, name='editar_usuario'),
    path('gerenciar/<int:user_id>/resetar-senha/', views.resetar_senha_usuario, name='resetar_senha_usuario'),
    path('gerenciar/<int:user_id>/toggle-ativo/', views.toggle_ativo_usuario, name='toggle_ativo_usuario'),
    path('promover/<int:user_id>/', views.promover_usuario, name='promover_usuario'),
    path('rebaixar/<int:user_id>/', views.rebaixar_usuario, name='rebaixar_usuario'),
    path('explorar/', views_explorar.explorar, name='explorar'),
    path('explorar/<int:user_id>/', views_explorar.perfil_usuario, name='perfil_usuario'),
]
