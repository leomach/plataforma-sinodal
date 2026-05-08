from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_eventos, name='lista_eventos'),
    path('gerenciar/', views.gerenciar_eventos, name='gerenciar_eventos'),
    path('novo/', views.criar_evento, name='criar_evento'),
    path('<slug:slug>/', views.detalhe_evento, name='detalhe_evento'),
    path('<slug:slug>/editar/', views.editar_evento, name='editar_evento'),
    path('<slug:slug>/campos/', views.gerenciar_campos_evento, name='gerenciar_campos_evento'),
    path('<slug:slug>/inscrever/', views.inscrever_evento, name='inscrever_evento'),
    path('<slug:slug>/inscricoes/', views.gerenciar_inscricoes, name='gerenciar_inscricoes'),
    path('<slug:slug>/hub/', views.hub_evento, name='hub_evento'),
    path('validar/<int:inscricao_id>/<str:acao>/', views.validar_inscricao, name='validar_inscricao'),
]
