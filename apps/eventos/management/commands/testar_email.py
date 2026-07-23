from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = (
        'Envia um e-mail de teste para validar a configuração de envio '
        '(backend, provedor e remetente). Use em produção para confirmar '
        'que as notificações automáticas funcionam na Railway.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            'destinatario',
            help='Endereço de e-mail que receberá a mensagem de teste.',
        )

    def handle(self, *args, **options):
        destinatario = options['destinatario']

        self.stdout.write('Configuração atual:')
        self.stdout.write(f'  EMAIL_BACKEND     = {settings.EMAIL_BACKEND}')
        self.stdout.write(f'  DEFAULT_FROM_EMAIL = {settings.DEFAULT_FROM_EMAIL}')
        resend_key = settings.ANYMAIL.get('RESEND_API_KEY', '')
        self.stdout.write(
            f'  RESEND_API_KEY    = {"(definida)" if resend_key else "(vazia)"}'
        )
        self.stdout.write(f'Enviando e-mail de teste para {destinatario}...')

        try:
            enviados = send_mail(
                subject='[Plataforma Sinodal] E-mail de teste',
                message=(
                    'Este é um e-mail de teste da Plataforma Sinodal. '
                    'Se você recebeu esta mensagem, o envio automático está funcionando.'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[destinatario],
                html_message=(
                    '<p>Este é um <strong>e-mail de teste</strong> da Plataforma Sinodal.</p>'
                    '<p>Se você recebeu esta mensagem, o envio automático está funcionando. ✅</p>'
                ),
                fail_silently=False,
            )
        except Exception as exc:
            raise CommandError(f'Falha ao enviar: {exc}') from exc

        if enviados:
            self.stdout.write(self.style.SUCCESS(
                f'✓ E-mail aceito pelo provedor ({enviados} envio(s)). '
                'Verifique a caixa de entrada (e o spam).'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                '⚠ O backend retornou 0 envios. Revise as credenciais/remetente.'
            ))
