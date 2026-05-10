from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from core import constants
from core.mixins import ImageCleanupMixin

class User(ImageCleanupMixin, AbstractUser):
    image_fields = ['foto']
    tipo = models.IntegerField(
        _('Tipo de Usuário'),
        choices=constants.TIPO_USUARIO_CHOICES,
        default=constants.SOCIO,
    )
    foto = models.ImageField(_('Foto de Perfil'), upload_to='usuarios/fotos/', blank=True, null=True)
    bio = models.TextField(_('Bio'), max_length=500, blank=True)
    whatsapp = models.CharField(_('WhatsApp'), max_length=20, blank=True, help_text=_('Inclua o DDD (ex: 11988887777)'))
    
    @property
    def display_name(self):
        if self.first_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.username

    @property
    def short_name(self):
        return self.first_name if self.first_name else self.username

    @property
    def perfil_completo(self):
        return all([self.first_name, self.last_name, self.email, self.whatsapp])

    def __str__(self):
        return f"{self.display_name} ({self.get_tipo_display()})"
