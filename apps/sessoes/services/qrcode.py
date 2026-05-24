import io
import uuid

import segno


def gerar_token() -> str:
    return f"SINODAL-{uuid.uuid4().hex}"


def gerar_qrcode_svg(token: str) -> str:
    qr = segno.make(token, error='M')
    buf = io.BytesIO()
    qr.save(buf, kind='svg', scale=5, xmldecl=False, svgns=False, svgclass=None, nl=False)
    return buf.getvalue().decode('utf-8')


def invalidar_e_regenerar(inscricao) -> 'CredencialQRCode':
    from apps.sessoes.models import CredencialQRCode
    try:
        qr_antigo = inscricao.qr_code
        qr_antigo.ativo = False
        qr_antigo.save(update_fields=['ativo'])
        qr_antigo.delete()
    except CredencialQRCode.DoesNotExist:
        pass
    return CredencialQRCode.objects.create(
        inscricao=inscricao,
        token=gerar_token(),
    )
