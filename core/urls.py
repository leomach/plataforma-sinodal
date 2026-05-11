from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.usuarios import views as usuario_views
from apps.eventos import views as evento_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', usuario_views.home, name='home'),
    path('usuarios/', include('apps.usuarios.urls')),
    path('eventos/', include('apps.eventos.urls')),
    path('hub/', include('apps.hub.urls')),
    path('webhooks/infinitepay/<str:token>/', evento_views.webhook_infinitepay, name='webhook_infinitepay'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
