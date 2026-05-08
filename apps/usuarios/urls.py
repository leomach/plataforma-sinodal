from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='usuarios/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('perfil/', views.perfil, name='perfil'),
    path('gerenciar/', views.gerenciar_usuarios, name='gerenciar_usuarios'),
    path('promover/<int:user_id>/', views.promover_usuario, name='promover_usuario'),
    path('rebaixar/<int:user_id>/', views.rebaixar_usuario, name='rebaixar_usuario'),
]
