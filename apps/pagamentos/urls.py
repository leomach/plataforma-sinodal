from django.urls import path

from . import views

urlpatterns = [
    path(
        'webhooks/infinitepay/<str:token>/',
        views.webhook_infinitepay,
        name='webhook_infinitepay',
    ),
]
