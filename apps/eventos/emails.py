import logging

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

logger = logging.getLogger(__name__)


def _send(assunto, template, context, destinatario):
    if not destinatario:
        logger.warning("E-mail '%s' não enviado: destinatário vazio.", assunto)
        return
    html = render_to_string(template, context)
    # fail_silently=False para capturarmos e registrarmos a falha aqui, sem
    # deixar o erro estourar na request do usuário. Assim as falhas ficam
    # visíveis nos logs da Railway em vez de sumirem silenciosamente.
    try:
        enviados = send_mail(
            subject=assunto,
            message='',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[destinatario],
            html_message=html,
            fail_silently=False,
        )
    except Exception:
        logger.exception("Falha ao enviar e-mail '%s' para %s", assunto, destinatario)
        return
    if not enviados:
        logger.warning("E-mail '%s' para %s retornou 0 envios.", assunto, destinatario)
    else:
        logger.info("E-mail '%s' enviado para %s.", assunto, destinatario)


def enviar_pagamento_confirmado(inscricao):
    _send(
        assunto=f'[Plataforma Sinodal] Pagamento confirmado — {inscricao.evento.titulo}',
        template='emails/pagamento_confirmado.html',
        context={'inscricao': inscricao},
        destinatario=inscricao.usuario.email,
    )


def enviar_credencial_validada(inscricao):
    _send(
        assunto=f'[Plataforma Sinodal] Credencial validada — {inscricao.evento.titulo}',
        template='emails/credencial_validada.html',
        context={'inscricao': inscricao},
        destinatario=inscricao.usuario.email,
    )


def enviar_inscricao_aprovada(inscricao):
    _send(
        assunto=f'[Plataforma Sinodal] Inscrição aprovada — {inscricao.evento.titulo}',
        template='emails/inscricao_aprovada.html',
        context={'inscricao': inscricao},
        destinatario=inscricao.usuario.email,
    )
