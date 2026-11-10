from django.db import models
from django.conf import settings
from apps.recetas.models import Receta, ItemReceta
from apps.inventario.models import Lote


class TipoFlujoDespacho(models.TextChoices):
    GRATUITO = 'GRATUITO', 'Flujo Gratuito (Público)'
    PAGO = 'PAGO', 'Flujo de Pago (Privado)'
    MIXTO = 'MIXTO', 'Flujo Mixto'


class EstadoDespacho(models.TextChoices):
    EN_PROCESO = 'EN_PROCESO', 'En Proceso'
    COMPLETADO = 'COMPLETADO', 'Completado'
    CANCELADO = 'CANCELADO', 'Cancelado'


class Despacho(models.Model):
    receta = models.ForeignKey(Receta, on_delete=models.PROTECT, related_name='despachos')
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='despachos_realizados',
        help_text='Estudiante o usuario que efectúa la dispensación'
    )
    tipo_flujo = models.CharField(
        max_length=20,
        choices=TipoFlujoDespacho.choices,
        default=TipoFlujoDespacho.GRATUITO
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoDespacho.choices,
        default=EstadoDespacho.COMPLETADO
    )
    fecha_hora = models.DateTimeField(auto_now_add=True)
    autorizado_por_quimico = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='autorizaciones_controlados',
        help_text='Obligatorio para recetas que incluyan medicamentos controlados'
    )

    class Meta:
        verbose_name = 'Despacho'
        verbose_name_plural = 'Despachos'
        ordering = ['-fecha_hora']

    def __str__(self):
        return f"Despacho #{self.id} - {self.receta.paciente.nombre} ({self.get_tipo_flujo_display()})"


class DetalleDespacho(models.Model):
    despacho = models.ForeignKey(Despacho, on_delete=models.CASCADE, related_name='detalles')
    item_receta = models.ForeignKey(ItemReceta, on_delete=models.PROTECT, related_name='detalles_despacho')
    lote = models.ForeignKey(Lote, on_delete=models.PROTECT, related_name='detalles_despacho')
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    es_gratuito = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Detalle de Despacho'
        verbose_name_plural = 'Detalles de Despacho'

    def __str__(self):
        return f"{self.item_receta.producto.nombre} - Lote {self.lote.codigo} x {self.cantidad}"
