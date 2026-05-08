from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from core import constants

class Evento(models.Model):
    titulo = models.CharField(_('Título'), max_length=200)
    slug = models.SlugField(_('Slug'), unique=True, blank=True)
    descricao = models.TextField(_('Descrição'))
    categoria = models.IntegerField(_('Categoria'), choices=constants.CATEGORIA_EVENTO_CHOICES, default=constants.COMUNHAO)
    data_inicio = models.DateTimeField(_('Data de Início'))
    data_fim = models.DateTimeField(_('Data de Término'))
    local = models.CharField(_('Local'), max_length=255)
    banner = models.ImageField(_('Banner'), upload_to='eventos/banners/', blank=True, null=True)
    ativo = models.BooleanField(_('Ativo'), default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = _('Evento')
        verbose_name_plural = _('Eventos')
        ordering = ['-data_inicio']

class CampoEvento(models.Model):
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name='campos_personalizados')
    label = models.CharField(_('Pergunta'), max_length=255)
    tipo_campo = models.IntegerField(_('Tipo do Campo'), choices=constants.TIPO_CAMPO_CHOICES, default=constants.CAMPO_TEXTO)
    obrigatorio = models.BooleanField(_('Obrigatório'), default=True)
    opcoes = models.TextField(_('Opções (separadas por vírgula)'), blank=True, help_text=_('Apenas para campos de Seleção'))

    def __str__(self):
        return f"{self.label} ({self.evento.titulo})"

class Inscricao(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='inscricoes')
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name='inscritos')
    papel_evento = models.IntegerField(_('Papel no Evento'), choices=constants.PAPEL_EVENTO_CHOICES, default=constants.PAPEL_VISITANTE)
    status = models.IntegerField(_('Status'), choices=constants.STATUS_INSCRICAO_CHOICES, default=constants.STATUS_PENDENTE)
    credential_url = models.URLField(_('URL da Credencial (Drive)'), blank=True, null=True, help_text=_('Obrigatório para Delegados'))
    data_inscricao = models.DateTimeField(auto_now_add=True)
    observacoes = models.TextField(_('Observações'), blank=True)

    def __str__(self):
        return f"{self.usuario.short_name} - {self.evento.titulo}"

    class Meta:
        unique_together = ('usuario', 'evento')
        verbose_name = _('Inscrição')
        verbose_name_plural = _('Inscrições')

class RespostaInscricao(models.Model):
    inscricao = models.ForeignKey(Inscricao, on_delete=models.CASCADE, related_name='respostas')
    campo = models.ForeignKey(CampoEvento, on_delete=models.CASCADE)
    valor = models.TextField(_('Resposta'))

    def __str__(self):
        return f"Resposta de {self.inscricao.usuario.username} para {self.campo.label}"

class Sessao(models.Model):
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name='sessoes')
    nome = models.CharField(_('Nome da Sessão'), max_length=200)
    data_hora = models.DateTimeField(_('Data e Hora'))

    def __str__(self):
        return f"{self.nome} - {self.evento.titulo}"

    class Meta:
        verbose_name = _('Sessão')
        verbose_name_plural = _('Sessões')
        ordering = ['data_hora']

class Presenca(models.Model):
    sessao = models.ForeignKey(Sessao, on_delete=models.CASCADE, related_name='presencas')
    inscricao = models.ForeignKey(Inscricao, on_delete=models.CASCADE, related_name='presencas_em_sessoes')
    presente = models.BooleanField(_('Presente'), default=False)

    class Meta:
        unique_together = ('sessao', 'inscricao')
        verbose_name = _('Presença')
        verbose_name_plural = _('Presenças')

class DocumentoEvento(models.Model):
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name='documentos')
    titulo = models.CharField(_('Título do Documento'), max_length=200)
    arquivo_url = models.URLField(_('URL do Arquivo (Drive)'))
    restrito_delegados = models.BooleanField(_('Restrito a Delegados'), default=False)

    def __str__(self):
        return f"{self.titulo} - {self.evento.titulo}"

    class Meta:
        verbose_name = _('Documento do Evento')
        verbose_name_plural = _('Documentos do Evento')
