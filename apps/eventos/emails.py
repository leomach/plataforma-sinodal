from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings


def _send(assunto, template, context, destinatario):
    if not destinatario:
        return
    html = render_to_string(template, context)
    send_mail(
        subject=assunto,
        message='',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[destinatario],
        html_message=html,
        fail_silently=True,
    )


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
