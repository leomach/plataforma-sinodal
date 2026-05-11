from django.urls import path
from . import views

urlpatterns = [
    path('<slug:slug>/', views.hub_evento, name='hub_evento'),
]
