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
    path('<slug:slug>/editar-inscricao/', views.editar_inscricao, name='editar_inscricao'),
    path('<slug:slug>/confirmacao/', views.confirmacao_inscricao, name='confirmacao_inscricao'),
    path('<slug:slug>/inscricoes/', views.gerenciar_inscricoes, name='gerenciar_inscricoes'),
    path('<slug:slug>/hub/', views.hub_evento, name='hub_evento'),
    # Ações de inscrição (liderança)
    path('inscricao/<int:inscricao_id>/confirmar-pagamento/', views.confirmar_pagamento, name='confirmar_pagamento'),
    path('inscricao/<int:inscricao_id>/validar-credencial/', views.validar_credencial, name='validar_credencial'),
    path('inscricao/<int:inscricao_id>/rejeitar/', views.rejeitar_inscricao, name='rejeitar_inscricao'),
    path('inscricao/<int:inscricao_id>/reativar/', views.reativar_inscricao, name='reativar_inscricao'),
    path('inscricao/<int:inscricao_id>/gerar-link/', views.gerar_link_pagamento, name='gerar_link_pagamento'),
]
