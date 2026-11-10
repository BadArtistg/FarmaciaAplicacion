from datetime import timedelta
import pytest
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.inventario.models import Producto, Lote, CondicionVenta
from apps.inventario.domain import StockInsuficienteException, LoteVencidoException
from apps.inventario.services import descontar_stock_fefo


@pytest.mark.django_db
class TestInventarioYFefo:

    def test_ingresar_lote_vencido_es_rechazado_caso_pf03(self):
        """
        Caso PF-03: Ingresar un lote con fecha vencida.
        Resultado esperado: El sistema lo rechaza con un mensaje claro.
        """
        hoy = timezone.localdate()
        fecha_ayer = hoy - timedelta(days=1)

        producto = Producto.objects.create(
            codigo='PAR-500',
            nombre='Paracetamol',
            forma_farmaceutica='Comprimidos',
            dosis='500 mg',
            precio=1200.00
        )

        lote_invalido = Lote(
            producto=producto,
            codigo='LOTE-VENCIDO-01',
            fecha_vencimiento=fecha_ayer,
            cantidad_inicial=50
        )

        with pytest.raises(ValidationError) as exc_info:
            lote_invalido.clean()

        assert 'fecha_vencimiento' in exc_info.value.message_dict
        assert 'No se puede registrar un lote con fecha vencida' in str(exc_info.value)

    def test_unicidad_de_lote_por_producto(self):
        """
        Restricción de unicidad: combinación producto + número de lote (Sección 5.2).
        """
        hoy = timezone.localdate()
        producto = Producto.objects.create(
            codigo='LOS-50',
            nombre='Losartán',
            forma_farmaceutica='Comprimidos',
            dosis='50 mg',
            precio=2500.00
        )

        Lote.objects.create(
            producto=producto,
            codigo='LOTE-DUPLICADO',
            fecha_vencimiento=hoy + timedelta(days=60),
            cantidad_inicial=100,
            cantidad_actual=100
        )

        with pytest.raises(IntegrityError):
            Lote.objects.create(
                producto=producto,
                codigo='LOTE-DUPLICADO',
                fecha_vencimiento=hoy + timedelta(days=120),
                cantidad_inicial=50,
                cantidad_actual=50
            )

    def test_algoritmo_fefo_identifica_lote_que_vence_primero(self):
        """
        Verificación de regla FEFO: el lote con fecha más próxima a vencer
        debe ser identificado como 'sale primero' automáticamente.
        """
        hoy = timezone.localdate()
        producto = Producto.objects.create(
            codigo='MET-850',
            nombre='Metformina',
            forma_farmaceutica='Comprimidos',
            dosis='850 mg',
            precio=1990.00
        )

        # Lote que vence en 180 días
        lote_lejano = Lote.objects.create(
            producto=producto,
            codigo='ME-LEJANO',
            fecha_vencimiento=hoy + timedelta(days=180),
            cantidad_inicial=100,
            cantidad_actual=100
        )

        # Lote que vence en 45 días
        lote_cercano = Lote.objects.create(
            producto=producto,
            codigo='ME-CERCANO',
            fecha_vencimiento=hoy + timedelta(days=45),
            cantidad_inicial=50,
            cantidad_actual=50
        )

        assert producto.lote_sale_primero.codigo == 'ME-CERCANO'
        assert producto.stock_total == 150

    def test_descuento_fefo_atomo_y_control_de_stock(self):
        """
        Verifica que al descontar stock se consuma primero el lote más cercano a vencer (FEFO),
        y que si se solicita más del stock total se lance StockInsuficienteException.
        """
        hoy = timezone.localdate()
        producto = Producto.objects.create(
            codigo='AMX-500',
            nombre='Amoxicilina',
            forma_farmaceutica='Cápsulas',
            dosis='500 mg',
            precio=3500.00
        )

        lote1 = Lote.objects.create(
            producto=producto,
            codigo='AMX-LOTE1',
            fecha_vencimiento=hoy + timedelta(days=30),  # Vence antes
            cantidad_inicial=30,
            cantidad_actual=30
        )

        lote2 = Lote.objects.create(
            producto=producto,
            codigo='AMX-LOTE2',
            fecha_vencimiento=hoy + timedelta(days=100), # Vence después
            cantidad_inicial=50,
            cantidad_actual=50
        )

        # Descontar 40 unidades: deben salir 30 del lote 1 y 10 del lote 2
        descontados = descontar_stock_fefo(producto, 40)

        lote1.refresh_from_db()
        lote2.refresh_from_db()

        assert lote1.cantidad_actual == 0
        assert lote2.cantidad_actual == 40
        assert producto.stock_total == 40
        # Ahora el lote que sale primero es lote2
        assert producto.lote_sale_primero.codigo == 'AMX-LOTE2'

        # Intentar descontar más del saldo disponible lanza excepción de dominio
        with pytest.raises(StockInsuficienteException):
            descontar_stock_fefo(producto, 50)
