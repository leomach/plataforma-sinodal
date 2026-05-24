from django.db import models
from django.db.models import Count, Q
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


class Sessao(models.Model):
    STATUS_EM_BREVE = 1
    STATUS_CHAMADA = 2
    STATUS_ABERTA = 3
    STATUS_ENCERRADA = 4

    STATUS_CHOICES = [
        (STATUS_EM_BREVE, 'Em Breve'),
        (STATUS_CHAMADA, 'Chamada'),
        (STATUS_ABERTA, 'Aberta'),
        (STATUS_ENCERRADA, 'Encerrada'),
    ]

    STATUS_ATIVOS = [STATUS_CHAMADA, STATUS_ABERTA]

    evento = models.ForeignKey(
        'eventos.Evento',
        on_delete=models.CASCADE,
        related_name='sessoes',
    )
    nome = models.CharField(_('Nome da Sessão'), max_length=200)
    data_hora = models.DateTimeField(_('Data e Hora'))
    status = models.PositiveSmallIntegerField(
        _('Status'),
        choices=STATUS_CHOICES,
        default=STATUS_EM_BREVE,
    )
    is_verificacao_poderes = models.BooleanField(
        _('Sessão de Verificação de Poderes'),
        default=False,
    )
    membros_extras = models.JSONField(
        _('Membros Extras da Mesa'),
        default=list,
        blank=True,
        help_text='Lista JSON de membros com cargos personalizados: [{inscricao_id, nome, cargo_descricao}]',
    )

    def __str__(self):
        return f"{self.nome} — {self.get_status_display()}"

    def clean(self):
        if not self.evento_id:
            return

        # Apenas uma sessão ativa (CHAMADA ou ABERTA) por evento
        if self.status in self.STATUS_ATIVOS:
            qs = Sessao.objects.filter(
                evento_id=self.evento_id,
                status__in=self.STATUS_ATIVOS,
            )
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError(
                    'Já existe uma sessão em Chamada ou Aberta neste evento. '
                    'Encerre-a antes de iniciar esta.'
                )

        # Apenas uma sessão de verificação de poderes por evento
        if self.is_verificacao_poderes:
            qs = Sessao.objects.filter(
                evento_id=self.evento_id,
                is_verificacao_poderes=True,
            )
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError(
                    {'is_verificacao_poderes': 'Já existe uma Sessão de Verificação de Poderes para este evento.'}
                )
            # Deve ser a primeira sessão do evento
            outras = Sessao.objects.filter(evento_id=self.evento_id)
            if self.pk:
                outras = outras.exclude(pk=self.pk)
            if outras.exists() and self.data_hora:
                minima = outras.order_by('data_hora').first()
                if minima and self.data_hora > minima.data_hora:
                    raise ValidationError(
                        {'is_verificacao_poderes': 'A Sessão de Verificação de Poderes deve ser a primeira do evento (data/hora mais antiga).'}
                    )

    def get_proxima_transicao(self):
        """Retorna o próximo status possível e o label do botão."""
        mapa = {
            self.STATUS_EM_BREVE: (self.STATUS_CHAMADA, 'Iniciar Chamada'),
            self.STATUS_CHAMADA: (self.STATUS_ABERTA, 'Abrir Sessão'),
            self.STATUS_ABERTA: (self.STATUS_ENCERRADA, 'Encerrar Sessão'),
        }
        return mapa.get(self.status)

    def pode_retroceder(self):
        """CHAMADA pode voltar para EM_BREVE."""
        return self.status == self.STATUS_CHAMADA

    class Meta:
        verbose_name = _('Sessão')
        verbose_name_plural = _('Sessões')
        ordering = ['data_hora']
        indexes = [
            models.Index(fields=['evento_id', 'status'], name='sessao_evento_status_idx'),
        ]


class CredencialQRCode(models.Model):
    inscricao = models.OneToOneField(
        'eventos.Inscricao',
        on_delete=models.CASCADE,
        related_name='qr_code',
    )
    token = models.CharField(max_length=64, unique=True, db_index=True)
    gerado_em = models.DateTimeField(auto_now_add=True)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"QR — {self.inscricao}"

    class Meta:
        verbose_name = _('Credencial QR Code')
        verbose_name_plural = _('Credenciais QR Code')


class Presenca(models.Model):
    sessao = models.ForeignKey(
        Sessao,
        on_delete=models.CASCADE,
        related_name='presencas',
    )
    inscricao = models.ForeignKey(
        'eventos.Inscricao',
        on_delete=models.CASCADE,
        related_name='presencas_sessoes',
    )
    presente = models.BooleanField(_('Presente'), default=False)
    ultima_atualizacao = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.inscricao} — {'Presente' if self.presente else 'Ausente'}"

    class Meta:
        verbose_name = _('Presença')
        verbose_name_plural = _('Presenças')
        unique_together = [('sessao', 'inscricao')]
        indexes = [
            # Usado em calcular_presentes() e contagem_presenca()
            models.Index(fields=['sessao_id', 'presente'], name='presenca_sessao_presente_idx'),
        ]


class Votacao(models.Model):
    STATUS_ABERTA = 1
    STATUS_EMPATADA = 2
    STATUS_ENCERRADA = 3

    STATUS_CHOICES = [
        (STATUS_ABERTA, 'Aberta'),
        (STATUS_EMPATADA, 'Aguardando Voto de Minerva'),
        (STATUS_ENCERRADA, 'Encerrada'),
    ]

    RESULTADO_APROVADA = 1
    RESULTADO_REJEITADA = 2

    RESULTADO_CHOICES = [
        (RESULTADO_APROVADA, 'Aprovada'),
        (RESULTADO_REJEITADA, 'Rejeitada'),
    ]

    sessao = models.ForeignKey(
        Sessao,
        on_delete=models.CASCADE,
        related_name='votacoes',
    )
    titulo = models.CharField(_('Proposta / Título'), max_length=500)
    status = models.PositiveSmallIntegerField(
        _('Status'),
        choices=STATUS_CHOICES,
        default=STATUS_ABERTA,
    )
    resultado = models.PositiveSmallIntegerField(
        _('Resultado'),
        choices=RESULTADO_CHOICES,
        null=True,
        blank=True,
    )
    voto_minerva_favor = models.BooleanField(
        _('Voto de Minerva — A Favor'),
        null=True,
        blank=True,
    )
    minerva_por = models.ForeignKey(
        'usuarios.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='votos_minerva',
    )
    criada_em = models.DateTimeField(auto_now_add=True)
    encerrada_em = models.DateTimeField(null=True, blank=True)

    def contagem(self):
        # Se votos já estiverem prefetchados, usa Python (zero queries extras)
        if hasattr(self, '_prefetched_objects_cache') and 'votos' in self._prefetched_objects_cache:
            votos = self._prefetched_objects_cache['votos']
            return {
                'favor': sum(1 for v in votos if v.voto == VotoParticipante.VOTO_FAVOR),
                'contra': sum(1 for v in votos if v.voto == VotoParticipante.VOTO_CONTRA),
                'abstencoes': sum(1 for v in votos if v.voto == VotoParticipante.VOTO_ABSTER),
            }
        # Uma única query agregada em vez de 3 count() separados
        return self.votos.aggregate(
            favor=Count('pk', filter=Q(voto=VotoParticipante.VOTO_FAVOR)),
            contra=Count('pk', filter=Q(voto=VotoParticipante.VOTO_CONTRA)),
            abstencoes=Count('pk', filter=Q(voto=VotoParticipante.VOTO_ABSTER)),
        )

    def __str__(self):
        return f"{self.titulo} ({self.get_status_display()})"

    class Meta:
        verbose_name = _('Votação')
        verbose_name_plural = _('Votações')
        ordering = ['-criada_em']
        indexes = [
            models.Index(fields=['sessao_id', 'status'], name='votacao_sessao_status_idx'),
        ]


class VotoParticipante(models.Model):
    VOTO_FAVOR = 1
    VOTO_CONTRA = 2
    VOTO_ABSTER = 3

    VOTO_CHOICES = [
        (VOTO_FAVOR, 'A Favor'),
        (VOTO_CONTRA, 'Contra'),
        (VOTO_ABSTER, 'Abster-se'),
    ]

    votacao = models.ForeignKey(
        Votacao,
        on_delete=models.CASCADE,
        related_name='votos',
    )
    inscricao = models.ForeignKey(
        'eventos.Inscricao',
        on_delete=models.CASCADE,
        related_name='votos_participante',
    )
    voto = models.PositiveSmallIntegerField(_('Voto'), choices=VOTO_CHOICES)
    votado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.inscricao} — {self.get_voto_display()}"

    class Meta:
        verbose_name = _('Voto')
        verbose_name_plural = _('Votos')
        unique_together = [('votacao', 'inscricao')]


class EventoLog(models.Model):
    TIPO_AUTO = 1
    TIPO_MANUAL = 2

    TIPO_CHOICES = [
        (TIPO_AUTO, 'Automático'),
        (TIPO_MANUAL, 'Manual'),
    ]

    sessao = models.ForeignKey(
        Sessao,
        on_delete=models.CASCADE,
        related_name='logs',
    )
    tipo = models.PositiveSmallIntegerField(
        _('Tipo'),
        choices=TIPO_CHOICES,
        default=TIPO_AUTO,
    )
    descricao = models.TextField(_('Descrição'))
    timestamp = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(
        'usuarios.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs_sessao',
    )

    def __str__(self):
        return f"[{self.get_tipo_display()}] {self.descricao[:60]}"

    class Meta:
        verbose_name = _('Log da Sessão')
        verbose_name_plural = _('Logs das Sessões')
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['sessao_id', 'timestamp'], name='log_sessao_timestamp_idx'),
        ]


class MembroDaMesa(models.Model):
    PRESIDENTE = 1
    VICE_PRESIDENTE = 2
    PRIMEIRO_SECRETARIO = 3
    SEGUNDO_SECRETARIO = 4
    TESOUREIRO = 5
    SECRETARIO_EXECUTIVO = 6

    CARGO_CHOICES = [
        (PRESIDENTE, 'Presidente da Mesa'),
        (VICE_PRESIDENTE, 'Vice-Presidente'),
        (PRIMEIRO_SECRETARIO, '1º Secretário'),
        (SEGUNDO_SECRETARIO, '2º Secretário'),
        (TESOUREIRO, 'Tesoureiro'),
        (SECRETARIO_EXECUTIVO, 'Secretário Executivo'),
    ]

    sessao = models.ForeignKey(
        Sessao,
        on_delete=models.CASCADE,
        related_name='membros_mesa',
    )
    inscricao = models.ForeignKey(
        'eventos.Inscricao',
        on_delete=models.CASCADE,
        related_name='cargos_mesa',
    )
    cargo = models.PositiveSmallIntegerField(
        _('Cargo'),
        choices=CARGO_CHOICES,
    )
    assumiu_em = models.DateTimeField(auto_now_add=True)
    encerrou_em = models.DateTimeField(null=True, blank=True)

    @property
    def ativo(self):
        return self.encerrou_em is None

    @property
    def cargo_label(self):
        return self.get_cargo_display()

    def __str__(self):
        nome = self.inscricao.usuario.get_full_name() or self.inscricao.usuario.username
        return f"{nome} — {self.cargo_label}"

    class Meta:
        verbose_name = _('Membro da Mesa')
        verbose_name_plural = _('Mesa Diretora')
        ordering = ['cargo', 'assumiu_em']
        indexes = [
            # Usado em todas as queries de mesa ativa
            models.Index(fields=['sessao_id', 'encerrou_em'], name='mesa_sessao_ativa_idx'),
        ]
