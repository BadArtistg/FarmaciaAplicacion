import base64

try:
    import pyotp
except ImportError:
    pyotp = None

from django.conf import settings
from django.contrib.auth import authenticate, login
from .models import Usuario, AuditoriaEvento, RolUsuario


def obtener_ip_cliente(request) -> str:
    if not request:
        return '127.0.0.1'
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
    return ip


def registrar_auditoria(
    accion: str,
    entidad: str,
    usuario=None,
    detalle: dict = None,
    request=None
) -> AuditoriaEvento:
    """Registra un evento inmutable en la bitácora de auditoría."""
    ip = obtener_ip_cliente(request)
    user_obj = None
    usuario_str = 'Sistema'

    if usuario and getattr(usuario, 'is_authenticated', False):
        user_obj = usuario
        usuario_str = usuario.username
    elif isinstance(usuario, Usuario):
        user_obj = usuario
        usuario_str = usuario.username
    elif isinstance(usuario, str):
        usuario_str = usuario

    evento = AuditoriaEvento.objects.create(
        usuario=user_obj,
        usuario_str=usuario_str,
        accion=accion,
        entidad=entidad,
        ip=ip,
        detalle=detalle or {}
    )
    return evento


def validar_codigo_totp(usuario: Usuario, codigo: str) -> bool:
    """
    Valida el código de segundo factor.
    En entorno de práctica/docencia, permite el código ficticio documentado '123456'.
    Si tiene secreto OTP configurado y la librería pyotp está disponible, verifica el TOTP estándar.
    """
    codigo = (codigo or '').strip()
    modo_practica = getattr(settings, 'MODO_PRACTICA', True)
    codigo_practica = getattr(settings, 'CODIGO_2FA_PRACTICA', '123456')

    if modo_practica and codigo == codigo_practica:
        return True

    if usuario.secreto_otp:
        try:
            import pyotp
            totp = pyotp.TOTP(usuario.secreto_otp)
            return totp.verify(codigo, valid_window=1)
        except Exception:
            pass

    return False
