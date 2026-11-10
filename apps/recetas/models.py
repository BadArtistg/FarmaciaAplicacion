from django.db import models
from django.conf import settings
from apps.inventario.models import Producto


class TipoCliente(models.TextChoices):
    PROGRAMA_PUBLICO = 'PROGRAMA', 'Programa Público (Gratuito)'
    PARTICULAR = 'PARTICULAR', 'Particular (Pago directo)'
    CONVENIO = 'CONVENIO', 'Convenio Institucional'


class Paciente(models.Model):
    nombre = models.CharField(max_length=200)
    rut_ficticio = models.CharField(max_length=15, unique=True, help_text='RUT de práctica para simulación')
    tipo_cliente = models.CharField(
        max_length=20,
        choices=TipoCliente.choices,
        default=TipoCliente.PROGRAMA_PUBLICO
    )
    telefono = models.CharField(max_length=20, blank=True)
    creado_el = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Paciente (Ficticio)'
        verbose_name_plural = 'Pacientes (Ficticios)'

    def __str__(self):
        return f"{self.nombre} ({self.rut_ficticio}) - {self.get_tipo_cliente_display()}"


class CupoPrograma(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='cupos')
    programa = models.CharField(max_length=100, help_text='Ej. Paciente Crónico, GES/AUGE')
    cantidad_mensual = models.PositiveIntegerField(help_text='Total unidades mensuales con cobertura 100% gratuita')
    cantidad_usada = models.PositiveIntegerField(default=0)
    vigente_hasta = models.DateField()

    class Meta:
        verbose_name = 'Cupo de Programa'
        verbose_name_plural = 'Cupos de Programas'

    @property
    def cupo_disponible(self) -> int:
        return max(0, self.cantidad_mensual - self.cantidad_usada)

    def consumir(self, cantidad: int) -> int:
        if cantidad > self.cupo_disponible:
            raise ValueError("La cantidad solicitada supera el cupo mensual disponible.")
        self.cantidad_usada += cantidad
        self.save(update_fields=['cantidad_usada'])
        return self.cantidad_usada

    def __str__(self):
        return f"Cupo {self.programa} para {self.paciente.nombre}: {self.cupo_disponible}/{self.cantidad_mensual} u."


class EstadoReceta(models.TextChoices):
    PENDIENTE = 'PENDIENTE', 'Pendiente de Dispensación'
    EN_PROCESO = 'EN_PROCESO', 'En Proceso'
    DISPENSADA = 'DISPENSADA', 'Dispensada Totalmente'
    RECHAZADA = 'RECHAZADA', 'Rechazada'


class Receta(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='recetas')
    medico = models.CharField(max_length=200, help_text='Nombre del médico prescriptor')
    fecha = models.DateField()
    estado = models.CharField(
        max_length=20,
        choices=EstadoReceta.choices,
        default=EstadoReceta.PENDIENTE
    )
    observaciones = models.TextField(blank=True)
    creado_el = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Receta'
        verbose_name_plural = 'Recetas'

    def __str__(self):
        return f"Receta #{self.id} - {self.paciente.nombre} ({self.get_estado_display()})"


class ModalidadItem(models.TextChoices):
    GRATUITO = 'GRATUITO', 'Gratuito (Cubierto por Programa)'
    PAGO = 'PAGO', 'De Pago (Excedente o Particular)'


class ItemReceta(models.Model):
    receta = models.ForeignKey(Receta, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='items_receta')
    cantidad_prescrita = models.PositiveIntegerField()
    modalidad = models.CharField(
        max_length=20,
        choices=ModalidadItem.choices,
        default=ModalidadItem.GRATUITO
    )
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        verbose_name = 'Ítem de Receta'
        verbose_name_plural = 'Ítems de Receta'

    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad_prescrita} ({self.get_modalidad_display()})"
