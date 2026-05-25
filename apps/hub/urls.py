from django.urls import include, path

from . import views, views_explorar

urlpatterns = [
    path('explorar/', views_explorar.explorar, name='explorar'),
    path('explorar/<int:user_id>/', views_explorar.perfil_usuario, name='perfil_usuario'),

    path('<slug:slug>/', views.hub_evento, name='hub_evento'),
    path('<slug:slug>/', include('apps.sessoes.urls')),
    path('<slug:slug>/documentos/', views.gerenciar_documentos, name='gerenciar_documentos_hub'),
    path('<slug:slug>/documentos/ata-rapida/', views.lancar_ata_rapida, name='lancar_ata_rapida'),
    path('documento/<int:pk>/excluir/', views.excluir_documento, name='excluir_documento_hub'),
]
