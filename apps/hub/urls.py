from django.urls import path
from . import views

urlpatterns = [
    path('<slug:slug>/', views.hub_evento, name='hub_evento'),
    path('<slug:slug>/documentos/', views.gerenciar_documentos, name='gerenciar_documentos_hub'),
    path('<slug:slug>/documentos/ata-rapida/', views.lancar_ata_rapida, name='lancar_ata_rapida'),
    path('documento/<int:pk>/excluir/', views.excluir_documento, name='excluir_documento_hub'),
]
