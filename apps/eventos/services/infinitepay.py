"""Wrapper de compatibilidade.

A integração real vive em `apps.pagamentos.services.infinitepay`. Este módulo
mantém a assinatura usada pelas views do app `eventos` para minimizar churn.
"""
from apps.pagamentos.services import infinitepay as _ip


def criar_link(inscricao, redirect_url: str, webhook_url: str) -> dict:
    """Cria link de pagamento para uma inscrição."""
    return _ip.criar_link(
        order_nsu=f'inscricao-{inscricao.id}',
        descricao=f'Inscrição — {inscricao.evento.titulo}',
        valor=inscricao.evento.valor_inscricao,
        customer_name=inscricao.usuario.display_name,
        customer_email=inscricao.usuario.email,
        redirect_url=redirect_url,
        webhook_url=webhook_url,
    )


def payment_check(inscricao) -> dict:
    """Consulta status de pagamento de uma inscrição na InfinitePay."""
    return _ip.payment_check(
        order_nsu=f'inscricao-{inscricao.id}',
        slug=inscricao.infinitepay_link_id or '',
    )
