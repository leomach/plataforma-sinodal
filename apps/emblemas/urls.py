from django.urls import path
from . import views

urlpatterns = [
    # Painel
    path('', views.painel, name='premiacoes_painel'),

    # CRUD de emblemas
    path('novo/', views.criar_emblema, name='emblema_criar'),
    path('<int:emblema_id>/editar/', views.editar_emblema, name='emblema_editar'),
    path('<int:emblema_id>/excluir/', views.excluir_emblema, name='emblema_excluir'),

    # Seleção e publicação
    path('<int:emblema_id>/selecionar/', views.selecionar_destinatarios, name='emblema_selecionar'),
    path('<int:emblema_id>/publicar/', views.publicar_emblema_view, name='emblema_publicar'),

    # Notificação
    path('notificacao/<int:conquista_id>/lida/', views.marcar_notificacao_lida, name='emblema_marcar_lido'),

    # Catálogo de templates
    path('catalogo/', views.catalogo, name='emblema_catalogo'),
    path('catalogo/novo/', views.catalogo_criar, name='catalogo_emblema_criar'),
    path('catalogo/<int:template_id>/editar/', views.catalogo_editar, name='catalogo_emblema_editar'),
    path('catalogo/<int:template_id>/excluir/', views.catalogo_excluir, name='catalogo_emblema_excluir'),
]
