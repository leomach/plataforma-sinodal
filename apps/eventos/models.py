from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from core import constants
from core.mixins import ImageCleanupMixin

class Evento(ImageCleanupMixin, models.Model):
    image_fields = ['banner']
    titulo = models.CharField(_('Título'), max_length=200)
    slug = models.SlugField(_('Slug'), unique=True, blank=True)
    descricao = models.TextField(_('Descrição'))
    categoria = models.IntegerField(_('Categoria'), choices=constants.CATEGORIA_EVENTO_CHOICES, default=constants.COMUNHAO)
    data_inicio = models.DateTimeField(_('Data de Início'))
    data_fim = models.DateTimeField(_('Data de Término'))
    
    # Período de Inscrição
    inscricoes_inicio = models.DateTimeField(_('Início das Inscrições'), null=True, blank=True)
    inscricoes_fim = models.DateTimeField(_('Fim das Inscrições'), null=True, blank=True)
    
    local = models.CharField(_('Local'), max_length=255)
    banner = models.ImageField(_('Banner'), upload_to='eventos/banners/', blank=True, null=True)
    vagas = models.PositiveIntegerField(_('Quantidade de Vagas'), default=0, help_text=_('Deixe 0 para vagas ilimitadas'))
    tipo_financeiro = models.IntegerField(
        _('Tipo Financeiro'),
        choices=constants.TIPO_FINANCEIRO_CHOICES,
        default=constants.MANUAL,
    )
    
    # Configuração de Pagamento (Manual)
    valor_inscricao = models.DecimalField(_('Valor da Inscrição'), max_digits=10, decimal_places=2, default=0)
    chave_pix = models.CharField(_('Chave PIX para Recebimento'), max_length=255, blank=True)
    instrucoes_pagamento = models.TextField(_('Instruções de Pagamento'), blank=True)
    
    ativo = models.BooleanField(_('Ativo'), default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    @property
    def periodo_inscricao_aberto(self):
        agora = timezone.now()
        if self.inscricoes_inicio and agora < self.inscricoes_inicio:
            return False
        if self.inscricoes_fim and agora > self.inscricoes_fim:
            return False
        return True

    @property
    def vagas_disponiveis(self):
        if self.vagas == 0:
            return float('inf')
        return self.vagas - self.inscritos.count()

    @property
    def esgotado(self):
        if self.vagas == 0:
            return False
        return self.inscritos.count() >= self.vagas

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
    
    # Validações Separadas (Dual Check)
    pago = models.BooleanField(_('Pagamento Confirmado'), default=False)
    data_pagamento = models.DateTimeField(_('Data do Pagamento'), null=True, blank=True)
    credencial_validada = models.BooleanField(_('Credencial Validada'), default=False)
    
    # Status Final (Mantido para compatibilidade, mas calculado ou setado manualmente)
    status = models.IntegerField(_('Status Final'), choices=constants.STATUS_INSCRICAO_CHOICES, default=constants.STATUS_PENDENTE)
    
    credential_url = models.URLField(_('URL da Credencial (Drive)'), max_length=500, blank=True, null=True)
    infinitepay_link_id = models.CharField(_('InfinitePay Invoice Slug'), max_length=100, blank=True)
    infinitepay_url = models.URLField(_('URL de Pagamento InfinitePay'), max_length=500, blank=True, null=True)
    data_inscricao = models.DateTimeField(auto_now_add=True)
    observacoes = models.TextField(_('Observações'), blank=True)
    
    validado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='validacoes_realizadas')

    def save(self, *args, **kwargs):
        # Não recalcula se foi rejeitado manualmente
        if self.status != constants.STATUS_REJEITADO:
            pago_ok = self.pago or self.evento.valor_inscricao == 0
            precisa_credencial = self.papel_evento in [constants.PAPEL_DELEGADO, constants.PAPEL_EX_OFFICIO]
            aprovado = (pago_ok and self.credencial_validada) if precisa_credencial else pago_ok
            self.status = constants.STATUS_APROVADO if aprovado else constants.STATUS_PENDENTE
        super().save(*args, **kwargs)

    @property
    def pode_acessar_hub(self):
        # Se for Gratuito, só precisa validar credencial se for delegado
        pago_check = True if self.evento.valor_inscricao == 0 else self.pago
        
        # Visitantes/Correspondentes: Só precisam pagar (se houver custo)
        if self.papel_evento in [constants.PAPEL_VISITANTE, constants.PAPEL_CORRESPONDENTE]:
            return pago_check
            
        # Delegados/Ex-Officio: Precisam pagar E validar credencial
        return pago_check and self.credencial_validada

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
    arquivo_url = models.URLField(_('URL do Arquivo (Drive)'), max_length=500)
    restrito_delegados = models.BooleanField(_('Restrito a Delegados'), default=False)

    def __str__(self):
        return f"{self.titulo} - {self.evento.titulo}"

    class Meta:
        verbose_name = _('Documento do Evento')
        verbose_name_plural = _('Documentos do Evento')
