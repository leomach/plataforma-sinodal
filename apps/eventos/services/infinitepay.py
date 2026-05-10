import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

_CHECKOUT_BASE = 'https://api.checkout.infinitepay.io'
_HEADERS = {'Content-Type': 'application/json'}


def criar_link(inscricao, redirect_url: str, webhook_url: str) -> dict:
    """Cria um link de pagamento no InfinitePay e retorna o dict com a resposta."""
    valor_centavos = int(inscricao.evento.valor_inscricao * 100)
    payload = {
        'handle': settings.INFINITEPAY_HANDLE,
        'order_nsu': f'inscricao-{inscricao.id}',
        'redirect_url': redirect_url,
        'webhook_url': webhook_url,
        'customer': {
            'name': inscricao.usuario.display_name,
            'email': inscricao.usuario.email,
        },
        'items': [
            {
                'quantity': 1,
                'price': valor_centavos,
                'description': f'Inscrição — {inscricao.evento.titulo}',
            }
        ],
    }
    resp = requests.post(
        f'{_CHECKOUT_BASE}/links',
        json=payload,
        headers=_HEADERS,
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def payment_check(inscricao) -> dict:
    """Consulta o status de pagamento de uma inscrição via InfinitePay."""
    payload = {
        'handle': settings.INFINITEPAY_HANDLE,
        'order_nsu': f'inscricao-{inscricao.id}',
    }
    if inscricao.infinitepay_link_id:
        payload['slug'] = inscricao.infinitepay_link_id

    resp = requests.post(
        f'{_CHECKOUT_BASE}/payment_check',
        json=payload,
        headers=_HEADERS,
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()
