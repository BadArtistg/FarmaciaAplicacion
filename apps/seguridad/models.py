from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings

class RolUsuario(models.TextChoices):
    ESTUDIANTE = 'ESTUDIANTE', 'Estudiante (Técnico en Farmacia)'
    CAJERO = 'CAJERO', 'Cajero'
    DOCENTE = 'DOCENTE', 'Docente a cargo'
    QUIMICO = 'QUIMICO', 'Químico farmacéutico'
    ADMIN = 'ADMIN', 'Administrador'


class Usuario(AbstractUser):
    rol = models.CharField(
        max_length=20,
        choices=RolUsuario.choices,
        default=RolUsuario.ESTUDIANTE,
        help_text='Rol para control de acceso basado en roles (RBAC)'
    )
    intentos_fallidos = models.PositiveIntegerField(
        default=0,
        help_text='Número consecutivo de intentos de login fallidos'
    )
    bloqueado = models.BooleanField(
        default=False,
        help_text='Indica si la cuenta fue bloqueada por superar el límite de intentos'
    )
    dos_factores_activo = models.BooleanField(
        default=False,
        help_text='Habilitación de segundo factor de autenticación TOTP'
    )
    secreto_otp = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        help_text='Secreto base32 para TOTP'
    )

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['username']

    @property
    def exige_2fa(self) -> bool:
        """
        Docente, químico y administrador deben usar 2FA obligatoriamente.
        También cualquier usuario que lo haya activado voluntariamente.
        """
        roles_con_2fa_obligatorio = {
            RolUsuario.DOCENTE,
            RolUsuario.QUIMICO,
            RolUsuario.ADMIN,
        }
        return self.rol in roles_con_2fa_obligatorio or self.dos_factores_activo

    def registrar_intento_fallido(self) -> bool:
        """
        Incrementa el contador. Si llega a MAX_INTENTOS_LOGIN (5), bloquea la cuenta.
        Retorna True si la cuenta fue bloqueada en esta llamada.
        """
        max_intentos = getattr(settings, 'MAX_INTENTOS_LOGIN', 5)
        self.intentos_fallidos += 1
        se_bloqueo = False
        if self.intentos_fallidos >= max_intentos:
            self.bloqueado = True
            self.is_active = False
            se_bloqueo = True
        self.save(update_fields=['intentos_fallidos', 'bloqueado', 'is_active'])
        return se_bloqueo

    def restablecer_intentos(self):
        """Reinicia el contador tras un login exitoso."""
        if self.intentos_fallidos > 0:
            self.intentos_fallidos = 0
            self.save(update_fields=['intentos_fallidos'])

    def desbloquear(self):
        """Desbloqueo administrativo de la cuenta."""
        self.bloqueado = False
        self.is_active = True
        self.intentos_fallidos = 0
        self.save(update_fields=['bloqueado', 'is_active', 'intentos_fallidos'])

    def __str__(self):
        return f"{self.username} ({self.get_rol_display()})"


class AuditoriaEvento(models.Model):
    """
    Bitácora inmutable de eventos del sistema (Sección 5 y 6.2 del informe).
    No permite UPDATE ni DELETE. Solo INSERT.
    """
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='eventos_auditoria'
    )
    usuario_str = models.CharField(
        max_length=150,
        blank=True,
        help_text='Nombre de usuario al momento del evento (para persistencia)'
    )
    accion = models.CharField(max_length=100)
    entidad = models.CharField(max_length=100)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    detalle = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = 'Evento de Auditoría'
        verbose_name_plural = 'Bitácora de Auditoría'
        ordering = ['-fecha_hora']

    def save(self, *args, **kwargs):
        # Garantía de inmutabilidad a nivel de ORM
        if self.pk is not None:
            raise ValidationError("La bitácora de auditoría es inmutable: no se permite modificar registros existentes.")
        if self.usuario and not self.usuario_str:
            self.usuario_str = self.usuario.username
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Garantía de inmutabilidad contra eliminación
        raise ValidationError("La bitácora de auditoría es inmutable: no se permite eliminar registros.")

    def __str__(self):
        usuario = self.usuario_str or 'Anónimo/Sistema'
        return f"[{self.fecha_hora:%Y-%m-%d %H:%M:%S}] {usuario} - {self.accion} ({self.entidad})"
