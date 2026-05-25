from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from core import constants as _c


class CatalogoEmblema(models.Model):
    """Template reutilizável criado e gerenciado pela liderança."""
    nome      = models.CharField(_('Nome'), max_length=60)
    icone     = models.CharField(_('Ícone'), max_length=10)
    descricao = models.CharField(_('Descrição'), max_length=200)
    categoria = models.CharField(
        _('Categoria'), max_length=30, choices=_c.EMBLEMA_CATEGORIA_CHOICES
    )
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='catalogo_emblemas_criados',
        verbose_name=_('Criado por'),
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    ativo     = models.BooleanField(_('Ativo'), default=True)

    class Meta:
        ordering = ['categoria', 'nome']
        verbose_name = _('Template de Emblema')
        verbose_name_plural = _('Catálogo de Emblemas')

    def __str__(self):
        return f'{self.icone} {self.nome}'


class Emblema(models.Model):
    STATUS_RASCUNHO  = _c.EMBLEMA_RASCUNHO
    STATUS_PUBLICADO = _c.EMBLEMA_PUBLICADO
    STATUS_CHOICES   = _c.EMBLEMA_STATUS_CHOICES

    # evento é OPCIONAL — null = emblema global (sem contexto de evento)
    evento = models.ForeignKey(
        'eventos.Evento',
        on_delete=models.SET_NULL,
        related_name='emblemas',
        null=True, blank=True,
        verbose_name=_('Evento'),
    )
    nome      = models.CharField(_('Nome'), max_length=60)
    icone     = models.CharField(_('Ícone'), max_length=10)
    descricao = models.CharField(_('Descrição'), max_length=200)
    categoria = models.CharField(
        _('Categoria'), max_length=30, choices=_c.EMBLEMA_CATEGORIA_CHOICES
    )
    status = models.PositiveSmallIntegerField(
        _('Status'), choices=STATUS_CHOICES, default=_c.EMBLEMA_RASCUNHO
    )
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='emblemas_criados',
        verbose_name=_('Criado por'),
    )
    criado_em    = models.DateTimeField(auto_now_add=True)
    publicado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = _('Emblema')
        verbose_name_plural = _('Emblemas')

    def __str__(self):
        contexto = f' · {self.evento.titulo}' if self.evento_id else ''
        return f'{self.icone} {self.nome}{contexto}'


class EmblemaUsuario(models.Model):
    emblema = models.ForeignKey(
        Emblema, on_delete=models.CASCADE, related_name='conquistas'
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='emblemas',
    )
    concedido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='emblemas_concedidos',
    )
    concedido_em = models.DateTimeField(auto_now_add=True)
    notificado   = models.BooleanField(default=False)

    class Meta:
        unique_together = [('emblema', 'usuario')]
        indexes = [
            models.Index(fields=['usuario', 'concedido_em']),
            models.Index(fields=['usuario', 'notificado']),
        ]
        verbose_name = _('Emblema do Usuário')
        verbose_name_plural = _('Emblemas dos Usuários')

    def __str__(self):
        return f'{self.emblema} → {self.usuario}'
