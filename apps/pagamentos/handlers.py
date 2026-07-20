"""Registry de handlers por prefixo de order_nsu.

Um app que quer participar do fluxo de pagamentos registra um handler:

    from apps.pagamentos.handlers import register_payment_handler

    @register_payment_handler('inscricao')
    def confirmar_inscricao(*, order_nsu, transacao, payload):
        ...

O webhook decide qual handler chamar com base no prefixo do order_nsu
(`inscricao-123` → handler 'inscricao').
"""
import logging

logger = logging.getLogger(__name__)

_HANDLERS: dict = {}


def register_payment_handler(prefix: str):
    """Decora função que processa pagamentos cujo order_nsu começa com `prefix`."""
    def decorator(func):
        if prefix in _HANDLERS:
            logger.warning(
                'pagamentos.handler.replacing',
                extra={'prefix': prefix, 'old': _HANDLERS[prefix].__name__, 'new': func.__name__},
            )
        _HANDLERS[prefix] = func
        return func
    return decorator


def dispatch_payment_confirmed(*, order_nsu: str, transacao, payload: dict):
    """Despacha confirmação de pagamento para o handler registrado.

    Retorna o resultado do handler, ou None se nenhum handler estiver registrado.
    """
    prefix = order_nsu.split('-', 1)[0] if '-' in order_nsu else order_nsu
    handler = _HANDLERS.get(prefix)
    if not handler:
        logger.warning(
            'pagamentos.handler.not_found',
            extra={'order_nsu': order_nsu, 'prefix': prefix},
        )
        return None
    return handler(order_nsu=order_nsu, transacao=transacao, payload=payload)


def get_registered_prefixes() -> list:
    return sorted(_HANDLERS.keys())
