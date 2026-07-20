"""Handlers de pagamento específicos do app `eventos`.

Registrados no `ready()` do EventosConfig.
"""
import logging

from django.utils import timezone

from apps.pagamentos.handlers import register_payment_handler
from apps.pagamentos.services import infinitepay as ip_service
from core import constants

from . import emails
from .models import Inscricao

logger = logging.getLogger(__name__)


@register_payment_handler('inscricao')
def confirmar_inscricao_paga(*, order_nsu, transacao, payload):
    """Processa confirmação de pagamento de uma inscrição em evento.

    order_nsu esperado: `inscricao-<id>`.
    """
    try:
        inscricao_id = int(order_nsu.split('-', 1)[1])
    except (ValueError, IndexError):
        logger.warning('eventos.handler.invalid_order_nsu', extra={'order_nsu': order_nsu})
        return

    try:
        inscricao = Inscricao.objects.select_related('usuario', 'evento').get(pk=inscricao_id)
    except Inscricao.DoesNotExist:
        logger.warning(
            'eventos.handler.inscricao_not_found',
            extra={'inscricao_id': inscricao_id, 'order_nsu': order_nsu},
        )
        return

    # Valida que o valor pago corresponde ao valor esperado da inscrição
    esperado_centavos = ip_service.to_centavos(inscricao.evento.valor_inscricao)
    pago_centavos = transacao.paid_amount_centavos

    if pago_centavos < esperado_centavos:
        logger.error(
            'eventos.handler.amount_mismatch',
            extra={
                'inscricao_id': inscricao_id,
                'esperado_centavos': esperado_centavos,
                'recebido_centavos': pago_centavos,
                'transaction_nsu': transacao.transaction_nsu,
            },
        )
        # Salva a transação como NÃO validada — fica para revisão manual
        return

    transacao.valor_validado = True
    transacao.save(update_fields=['valor_validado'])

    if inscricao.pago:
        logger.info(
            'eventos.handler.already_paid',
            extra={'inscricao_id': inscricao_id, 'transaction_nsu': transacao.transaction_nsu},
        )
        return

    status_anterior = inscricao.status
    inscricao.pago = True
    inscricao.data_pagamento = timezone.now()

    if not inscricao.infinitepay_link_id and transacao.invoice_slug:
        inscricao.infinitepay_link_id = transacao.invoice_slug

    inscricao.save()

    emails.enviar_pagamento_confirmado(inscricao)
    if (
        inscricao.status == constants.STATUS_APROVADO
        and status_anterior != constants.STATUS_APROVADO
    ):
        emails.enviar_inscricao_aprovada(inscricao)

    logger.info(
        'eventos.handler.confirmed',
        extra={
            'inscricao_id': inscricao_id,
            'transaction_nsu': transacao.transaction_nsu,
            'paid_amount_centavos': pago_centavos,
        },
    )
