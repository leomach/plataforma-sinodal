from django.db import models
from django.utils.translation import gettext_lazy as _


class TransacaoInfinitePay(models.Model):
    transaction_nsu = models.CharField(
        _('Transaction NSU'), max_length=100, unique=True, db_index=True,
    )
    invoice_slug = models.CharField(_('Invoice Slug'), max_length=100, blank=True, db_index=True)
    order_nsu = models.CharField(_('Order NSU'), max_length=100, db_index=True)

    amount_centavos = models.PositiveIntegerField(_('Valor em centavos'))
    paid_amount_centavos = models.PositiveIntegerField(_('Valor pago em centavos'))
    capture_method = models.CharField(_('Método'), max_length=20, blank=True)
    installments = models.PositiveSmallIntegerField(_('Parcelas'), default=1)
    receipt_url = models.URLField(_('URL do comprovante'), max_length=500, blank=True)

    payload_completo = models.JSONField(_('Payload completo'), default=dict, blank=True)

    valor_validado = models.BooleanField(_('Valor validado pelo handler'), default=False)
    payment_check_validado = models.BooleanField(
        _('Confirmado via payment_check'), default=False,
    )

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Transação InfinitePay')
        verbose_name_plural = _('Transações InfinitePay')
        ordering = ['-criado_em']

    def __str__(self):
        return f'{self.order_nsu} — {self.transaction_nsu}'

    @property
    def valor_reais(self):
        return self.paid_amount_centavos / 100

    @property
    def divergencia_valor(self) -> bool:
        return self.paid_amount_centavos < self.amount_centavos
