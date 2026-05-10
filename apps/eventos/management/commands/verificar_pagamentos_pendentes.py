from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.eventos.models import Inscricao
from apps.eventos.services import infinitepay as ip_service
from apps.eventos import emails
from core import constants


class Command(BaseCommand):
    help = 'Verifica pagamentos pendentes no InfinitePay e confirma automaticamente os que foram pagos.'

    def handle(self, *args, **options):
        pendentes = Inscricao.objects.filter(
            pago=False,
            evento__tipo_financeiro=constants.INFINITEPAY,
            infinitepay_url__isnull=False,
        ).exclude(
            status=constants.STATUS_REJEITADO,
        ).select_related('usuario', 'evento')

        total = pendentes.count()
        self.stdout.write(f'Verificando {total} inscrição(ões) pendentes de pagamento...')
        confirmados = 0

        for inscricao in pendentes:
            try:
                resultado = ip_service.payment_check(inscricao)
                if resultado.get('paid'):
                    status_anterior = inscricao.status
                    inscricao.pago = True
                    inscricao.data_pagamento = timezone.now()
                    inscricao.save()
                    confirmados += 1
                    self.stdout.write(self.style.SUCCESS(
                        f'  ✓ Pago: {inscricao.usuario.short_name} — {inscricao.evento.titulo}'
                    ))
                    if inscricao.status == constants.STATUS_APROVADO and status_anterior != constants.STATUS_APROVADO:
                        emails.enviar_inscricao_aprovada(inscricao)
            except Exception as exc:
                self.stderr.write(self.style.ERROR(
                    f'  ✗ Erro ao verificar inscrição {inscricao.id}: {exc}'
                ))

        self.stdout.write(f'\nConcluído: {confirmados}/{total} pagamentos confirmados.')
