from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class TipoDocumento(models.Model):
    nome = models.CharField(_('Nome do Tipo'), max_length=100)
    ordem = models.PositiveIntegerField(_('Ordem de Exibição'), default=0)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = _('Tipo de Documento')
        verbose_name_plural = _('Tipos de Documento')
        ordering = ['ordem', 'nome']

class Sessao(models.Model):
    evento = models.ForeignKey('eventos.Evento', on_delete=models.CASCADE, related_name='sessoes')
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
    inscricao = models.ForeignKey('eventos.Inscricao', on_delete=models.CASCADE, related_name='presencas_em_sessoes')
    presente = models.BooleanField(_('Presente'), default=False)

    class Meta:
        unique_together = ('sessao', 'inscricao')
        verbose_name = _('Presença')
        verbose_name_plural = _('Presenças')

class DocumentoEvento(models.Model):
    evento = models.ForeignKey('eventos.Evento', on_delete=models.CASCADE, related_name='documentos')
    tipo = models.ForeignKey(TipoDocumento, on_delete=models.PROTECT, related_name='documentos', null=True)
    titulo = models.CharField(_('Título do Documento'), max_length=200)
    arquivo_url = models.URLField(_('URL do Arquivo (Drive)'), max_length=500)
    restrito_delegados = models.BooleanField(_('Restrito a Delegados'), default=True)
    is_ata_sessao = models.BooleanField(_('É Ata da Sessão Atual?'), default=False)
    data_disponibilizacao = models.DateTimeField(_('Data de Disponibilização'), default=timezone.now)
    ordem = models.PositiveIntegerField(_('Ordem na Categoria'), default=0)

    def __str__(self):
        return f"{self.titulo} - {self.evento.titulo}"

    class Meta:
        verbose_name = _('Documento do Evento')
        verbose_name_plural = _('Documentos do Evento')
        ordering = ['-is_ata_sessao', 'tipo__ordem', 'ordem', '-data_disponibilizacao']
