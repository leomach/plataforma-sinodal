"""Webhook genérico InfinitePay.

Fluxo de segurança:
1. Valida token no path (defesa em profundidade)
2. Valida idempotência por transaction_nsu (chave única)
3. Chama payment_check para confirmar o pagamento de fato existe (anti-spoof)
4. Cria registro de transação ANTES de chamar o handler
5. Despacha para handler específico que valida o valor esperado
"""
import json
import logging

from django.conf import settings
from django.db import IntegrityError, transaction as db_transaction
from django.http import Http404, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .handlers import dispatch_payment_confirmed
from .models import TransacaoInfinitePay
from .services import infinitepay as ip_service

logger = logging.getLogger(__name__)


def _ok(message=None):
    return JsonResponse({'success': True, 'message': message})


def _bad(message, status=400):
    return JsonResponse({'success': False, 'message': message}, status=status)


@csrf_exempt
@require_POST
def webhook_infinitepay(request, token):
    # 1. Token no path
    if not settings.INFINITEPAY_WEBHOOK_SECRET or token != settings.INFINITEPAY_WEBHOOK_SECRET:
        raise Http404

    # 2. Parse do payload
    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        logger.warning('infinitepay.webhook.invalid_json')
        return _bad('invalid payload')

    order_nsu = (payload.get('order_nsu') or '').strip()
    transaction_nsu = (payload.get('transaction_nsu') or '').strip()
    invoice_slug = (payload.get('invoice_slug') or '').strip()

    if not order_nsu or not transaction_nsu:
        logger.warning(
            'infinitepay.webhook.missing_required_fields',
            extra={'order_nsu': order_nsu, 'transaction_nsu': transaction_nsu},
        )
        return _bad('missing required fields')

    # 3. Idempotência: se já processamos essa transação, retorna sucesso
    if TransacaoInfinitePay.objects.filter(transaction_nsu=transaction_nsu).exists():
        logger.info(
            'infinitepay.webhook.duplicate',
            extra={'transaction_nsu': transaction_nsu, 'order_nsu': order_nsu},
        )
        return _ok()

    # 4. Verificação anti-spoof: chama payment_check para confirmar com a InfinitePay
    try:
        check = ip_service.payment_check(
            order_nsu=order_nsu,
            slug=invoice_slug,
            transaction_nsu=transaction_nsu,
        )
    except Exception:
        logger.exception(
            'infinitepay.webhook.payment_check_failed',
            extra={'order_nsu': order_nsu, 'transaction_nsu': transaction_nsu},
        )
        # Retorna 400 para que a InfinitePay tente novamente
        return _bad('payment_check failed')

    if not check.get('paid'):
        logger.warning(
            'infinitepay.webhook.payment_check_negative',
            extra={
                'order_nsu': order_nsu,
                'transaction_nsu': transaction_nsu,
                'check_response': check,
            },
        )
        return _bad('payment not confirmed')

    amount = int(payload.get('amount') or check.get('amount') or 0)
    paid_amount = int(payload.get('paid_amount') or check.get('paid_amount') or 0)

    # 5. Cria transação + dispatcha handler em transação atômica
    try:
        with db_transaction.atomic():
            transacao = TransacaoInfinitePay.objects.create(
                transaction_nsu=transaction_nsu,
                invoice_slug=invoice_slug,
                order_nsu=order_nsu,
                amount_centavos=amount,
                paid_amount_centavos=paid_amount,
                capture_method=payload.get('capture_method') or check.get('capture_method') or '',
                installments=int(payload.get('installments') or check.get('installments') or 1),
                receipt_url=payload.get('receipt_url') or '',
                payload_completo=payload,
                payment_check_validado=True,
            )

            try:
                dispatch_payment_confirmed(
                    order_nsu=order_nsu, transacao=transacao, payload=payload,
                )
            except Exception:
                # Não queremos abortar a transação financeira só porque o handler
                # falhou (ex.: e-mail caiu). Registramos e seguimos — a transação
                # fica gravada e pode ser reprocessada manualmente.
                logger.exception(
                    'infinitepay.webhook.handler_failed',
                    extra={
                        'order_nsu': order_nsu,
                        'transaction_nsu': transaction_nsu,
                    },
                )
    except IntegrityError:
        # Race condition: webhook duplicado chegou em paralelo. Idempotência preservada.
        logger.info(
            'infinitepay.webhook.race_duplicate',
            extra={'transaction_nsu': transaction_nsu},
        )
        return _ok()

    logger.info(
        'infinitepay.webhook.confirmed',
        extra={
            'order_nsu': order_nsu,
            'transaction_nsu': transaction_nsu,
            'paid_amount_centavos': paid_amount,
            'capture_method': payload.get('capture_method'),
        },
    )
    return _ok()
