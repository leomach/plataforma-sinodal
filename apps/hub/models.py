from django.db import models
from django.utils.translation import gettext_lazy as _

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
    titulo = models.CharField(_('Título do Documento'), max_length=200)
    arquivo_url = models.URLField(_('URL do Arquivo (Drive)'), max_length=500)
    restrito_delegados = models.BooleanField(_('Restrito a Delegados'), default=False)

    def __str__(self):
        return f"{self.titulo} - {self.evento.titulo}"

    class Meta:
        verbose_name = _('Documento do Evento')
        verbose_name_plural = _('Documentos do Evento')
