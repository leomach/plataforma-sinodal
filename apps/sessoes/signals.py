from django.db.models.signals import post_save
from django.dispatch import receiver

from core import constants


@receiver(post_save, sender='eventos.Inscricao')
def gerar_qrcode_ao_aprovar(sender, instance, **kwargs):
    papeis_com_qr = [constants.PAPEL_DELEGADO, constants.PAPEL_EX_OFFICIO]
    if instance.status == constants.STATUS_APROVADO and instance.papel_evento in papeis_com_qr:
        from apps.sessoes.models import CredencialQRCode
        from apps.sessoes.services.qrcode import gerar_token
        CredencialQRCode.objects.get_or_create(
            inscricao=instance,
            defaults={'token': gerar_token()},
        )
