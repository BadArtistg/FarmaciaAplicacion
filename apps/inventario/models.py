from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from .domain import LoteVencidoException, StockInsuficienteException, validar_fecha_vencimiento_ingreso


class CondicionVenta(models.TextChoices):
    VENTA_DIRECTA = 'DIRECTA', 'Venta Directa (Sin Receta)'
    RECETA_SIMPLE = 'RECETA_SIMPLE', 'Receta Simple'
    RECETA_RETENIDA = 'RECETA_RETENIDA', 'Receta Retenida / Controlada'


class Producto(models.Model):
    codigo = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Código único del producto (SKU o código interno)'
    )
    nombre = models.CharField(max_length=200, help_text='Nombre comercial o genérico del medicamento')
    forma_farmaceutica = models.CharField(max_length=100, help_text='Ej. Comprimidos, Jarabe, Suspensión, Ampollas')
    dosis = models.CharField(max_length=100, help_text='Ej. 500 mg, 50 mg, 10 mg/5ml')
    condicion_venta = models.CharField(
        max_length=20,
        choices=CondicionVenta.choices,
        default=CondicionVenta.RECETA_SIMPLE
    )
    es_controlado = models.BooleanField(
        default=False,
        help_text='Indica si es un estupefaciente o psicotrópico que requiere autorización del químico farmacéutico'
    )
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Precio unitario referencial para cobro simulado'
    )
    stock_minimo = models.PositiveIntegerField(
        default=20,
        help_text='Nivel crítico de stock para activación de alertas'
    )
    creado_el = models.DateTimeField(auto_now_add=True)
    actualizado_el = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['nombre']

    @property
    def stock_total(self) -> int:
        """Suma de unidades disponibles en lotes activos y no vencidos."""
        hoy = timezone.localdate()
        total = self.lotes.filter(
            cantidad_actual__gt=0,
            fecha_vencimiento__gt=hoy
        ).aggregate(total=models.Sum('cantidad_actual'))['total']
        return total or 0

    @property
    def esta_en_stock_critico(self) -> bool:
        return self.stock_total <= self.stock_minimo

    @property
    def lote_sale_primero(self):
        """Retorna el lote que vence antes con stock disponible (algoritmo FEFO)."""
        hoy = timezone.localdate()
        return self.lotes.filter(
            cantidad_actual__gt=0,
            fecha_vencimiento__gt=hoy
        ).order_by('fecha_vencimiento').first()

    def lotes_orden_fefo(self):
        """Lista todos los lotes vigentes ordenados por vencimiento ascendente."""
        return self.lotes.all().order_by('fecha_vencimiento')

    def __str__(self):
        controlado = " [CONTROLADO]" if self.es_controlado else ""
        return f"{self.nombre} {self.dosis} ({self.forma_farmaceutica}){controlado}"


class Lote(models.Model):
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='lotes'
    )
    codigo = models.CharField(max_length=50, help_text='Número o identificador de lote de fabricación')
    fecha_vencimiento = models.DateField(help_text='Fecha de caducidad del lote')
    cantidad_inicial = models.PositiveIntegerField(help_text='Cantidad ingresada al lote')
    cantidad_actual = models.PositiveIntegerField(help_text='Saldo disponible en inventario')
    creado_el = models.DateTimeField(auto_now_add=True)
    actualizado_el = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Lote'
        verbose_name_plural = 'Lotes'
        unique_together = ('producto', 'codigo')
        ordering = ['fecha_vencimiento']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(cantidad_actual__gte=0),
                name='lote_cantidad_positiva'
            )
        ]

    def clean(self):
        # Validación de negocio: no admitir ingreso de lotes vencidos (PF-03)
        if self.pk is None and self.fecha_vencimiento:
            hoy = timezone.localdate()
            if self.fecha_vencimiento <= hoy:
                raise ValidationError({
                    'fecha_vencimiento': f'No se puede registrar un lote con fecha vencida ({self.fecha_vencimiento}). Debe ser posterior a hoy ({hoy}).'
                })
        if self.cantidad_inicial is not None and self.cantidad_actual is None:
            self.cantidad_actual = self.cantidad_inicial

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def esta_vencido(self) -> bool:
        return self.fecha_vencimiento <= timezone.localdate()

    @property
    def dias_para_vencer(self) -> int:
        delta = (self.fecha_vencimiento - timezone.localdate()).days
        return delta

    @property
    def por_vencer(self) -> bool:
        """Alerta ámbar: vence en los próximos 30 días y aún no vence."""
        dias = self.dias_para_vencer
        return 0 <= dias <= 30

    @property
    def estado_badge(self) -> dict:
        """Devuelve configuración de token visual y texto accesible."""
        if self.esta_vencido:
            return {'clase': 'badge-danger', 'texto': 'Vencido', 'icono': 'bi-exclamation-triangle-fill'}
        if self.por_vencer:
            return {'clase': 'badge-warning', 'texto': f'Por vencer ({self.dias_para_vencer} d)', 'icono': 'bi-clock-fill'}
        return {'clase': 'badge-success', 'texto': 'Vigente', 'icono': 'bi-check-circle-fill'}

    def descontar(self, cantidad: int) -> int:
        """
        Operación encapsulada del dominio:
        Descuenta cantidad del saldo actual del lote garantizando que nunca quede negativo.
        """
        if cantidad <= 0:
            raise ValueError("La cantidad a descontar debe ser mayor a 0.")
        if cantidad > self.cantidad_actual:
            raise StockInsuficienteException(self.producto.nombre, self.cantidad_actual, cantidad)
        self.cantidad_actual -= cantidad
        self.save(update_fields=['cantidad_actual', 'actualizado_el'])
        return self.cantidad_actual

    def __str__(self):
        return f"Lote {self.codigo} - {self.producto.nombre} (Vence: {self.fecha_vencimiento} | Stock: {self.cantidad_actual})"
