from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.usuarios import views as usuario_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', usuario_views.home, name='home'),
    path('usuarios/', include('apps.usuarios.urls')),
    path('eventos/', include('apps.eventos.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
