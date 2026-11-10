from django.db import models
from apps.dispensacion.models import Despacho


class EstadoPago(models.TextChoices):
    PENDIENTE = 'PENDIENTE', 'Pendiente'
    APROBADO = 'APROBADO', 'Aprobado'
    RECHAZADO = 'RECHAZADO', 'Rechazado'


class MedioPago(models.TextChoices):
    EFECTIVO = 'EFECTIVO', 'Efectivo Simulado'
    TARJETA_DEBITO = 'DEBITO', 'Tarjeta Débito Simulada'
    TARJETA_CREDITO = 'CREDITO', 'Tarjeta Crédito Simulada'
    CONVENIO = 'CONVENIO', 'Convenio Simulado'


class Pago(models.Model):
    despacho = models.ForeignKey(Despacho, on_delete=models.PROTECT, related_name='pagos')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    medio = models.CharField(max_length=20, choices=MedioPago.choices, default=MedioPago.EFECTIVO)
    estado = models.CharField(max_length=20, choices=EstadoPago.choices, default=EstadoPago.APROBADO)
    referencia = models.CharField(max_length=100, blank=True)
    respuesta_pasarela = models.JSONField(default=dict, blank=True)
    fecha_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'

    def __str__(self):
        return f"Pago {self.referencia or self.id} - ${self.monto} ({self.get_estado_display()})"


class Comprobante(models.Model):
    pago = models.OneToOneField(Pago, on_delete=models.CASCADE, related_name='comprobante')
    folio = models.CharField(max_length=50, unique=True)
    leyenda = models.CharField(
        max_length=255,
        default="Simulación – sin validez tributaria"
    )
    archivo_pdf = models.FileField(upload_to='comprobantes/', blank=True, null=True)
    fecha_emision = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Comprobante de Práctica'
        verbose_name_plural = 'Comprobantes de Práctica'

    def __str__(self):
        return f"Comprobante #{self.folio} ({self.leyenda})"
