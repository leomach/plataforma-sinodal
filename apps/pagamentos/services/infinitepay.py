"""Service genérico de integração com a InfinitePay (CloudWalk).

Documentação oficial: https://docs.infinitepay.io e
https://ajuda.infinitepay.io/pt-BR/articles/10766888-como-usar-o-checkout-da-infinitepay
"""
import logging
from decimal import Decimal, ROUND_HALF_UP

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

_CHECKOUT_BASE = 'https://api.checkout.infinitepay.io'


def _headers() -> dict:
    headers = {'Content-Type': 'application/json'}
    if getattr(settings, 'INFINITEPAY_SANDBOX', False):
        headers['Env'] = 'mock'
    return headers


def to_centavos(valor) -> int:
    """Converte Decimal/float/str para inteiro de centavos com arredondamento bancário."""
    if valor is None:
        return 0
    decimal_valor = Decimal(str(valor))
    return int(
        (decimal_valor * Decimal('100')).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    )


def criar_link(
    *,
    order_nsu: str,
    descricao: str,
    valor,
    customer_name: str,
    customer_email: str,
    redirect_url: str,
    webhook_url: str,
    customer_phone: str = '',
) -> dict:
    """Cria um link de pagamento no InfinitePay e retorna a resposta JSON.

    `valor` pode ser Decimal, float, int ou string — será convertido para centavos.
    """
    customer = {'name': customer_name, 'email': customer_email}
    if customer_phone:
        customer['phone_number'] = customer_phone

    payload = {
        'handle': settings.INFINITEPAY_HANDLE,
        'order_nsu': order_nsu,
        'redirect_url': redirect_url,
        'webhook_url': webhook_url,
        'customer': customer,
        'items': [
            {
                'quantity': 1,
                'price': to_centavos(valor),
                'description': descricao[:255],
            }
        ],
    }

    logger.info(
        'infinitepay.criar_link.requested',
        extra={'order_nsu': order_nsu, 'amount_centavos': payload['items'][0]['price']},
    )
    resp = requests.post(
        f'{_CHECKOUT_BASE}/links',
        json=payload,
        headers=_headers(),
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def payment_check(
    *,
    order_nsu: str = '',
    slug: str = '',
    transaction_nsu: str = '',
) -> dict:
    """Consulta o status de pagamento na InfinitePay.

    Aceita combinação de order_nsu, slug e transaction_nsu. Quanto mais
    parâmetros, mais preciso o lookup.
    """
    payload = {'handle': settings.INFINITEPAY_HANDLE}
    if order_nsu:
        payload['order_nsu'] = order_nsu
    if slug:
        payload['slug'] = slug
    if transaction_nsu:
        payload['transaction_nsu'] = transaction_nsu

    resp = requests.post(
        f'{_CHECKOUT_BASE}/payment_check',
        json=payload,
        headers=_headers(),
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()
