from datetime import timedelta
from typing import List, Tuple, Dict, Any
from django.db import transaction
from django.db.models import Sum, Q
from django.utils import timezone

from .models import Producto, Lote
from .domain import StockInsuficienteException, LoteVencidoException


def obtener_metricas_dashboard() -> Dict[str, Any]:
    """Genera las métricas principales de inventario y estado para el panel."""
    hoy = timezone.localdate()
    en_30_dias = hoy + timedelta(days=30)

    total_productos = Producto.objects.count()
    productos_controlados = Producto.objects.filter(es_controlado=True).count()

    total_unidades = Lote.objects.filter(
        cantidad_actual__gt=0,
        fecha_vencimiento__gt=hoy
    ).aggregate(total=Sum('cantidad_actual'))['total'] or 0

    lotes_por_vencer = Lote.objects.filter(
        cantidad_actual__gt=0,
        fecha_vencimiento__gt=hoy,
        fecha_vencimiento__lte=en_30_dias
    ).count()

    lotes_vencidos = Lote.objects.filter(
        fecha_vencimiento__lte=hoy,
        cantidad_actual__gt=0
    ).count()

    # Productos bajo stock mínimo
    productos = Producto.objects.all()
    productos_criticos = [p for p in productos if p.esta_en_stock_critico]

    return {
        'total_productos': total_productos,
        'productos_controlados': productos_controlados,
        'total_unidades': total_unidades,
        'lotes_por_vencer': lotes_por_vencer,
        'lotes_vencidos': lotes_vencidos,
        'productos_criticos_count': len(productos_criticos),
    }


def obtener_alertas_inventario() -> Dict[str, Any]:
    """Obtiene el listado detallado de alertas activas de stock y vencimiento."""
    hoy = timezone.localdate()
    en_30_dias = hoy + timedelta(days=30)

    # 1. Alertas de stock crítico
    productos = Producto.objects.all().prefetch_related('lotes')
    alertas_stock = []
    for p in productos:
        if p.esta_en_stock_critico:
            alertas_stock.append({
                'producto': p,
                'stock_actual': p.stock_total,
                'stock_minimo': p.stock_minimo,
                'tipo': 'danger' if p.stock_total == 0 else 'warning'
            })

    # 2. Alertas de lotes por vencer en los próximos 30 días
    lotes_por_vencer = Lote.objects.filter(
        cantidad_actual__gt=0,
        fecha_vencimiento__gt=hoy,
        fecha_vencimiento__lte=en_30_dias
    ).select_related('producto').order_by('fecha_vencimiento')

    # 3. Alertas de lotes vencidos con remanente
    lotes_vencidos = Lote.objects.filter(
        cantidad_actual__gt=0,
        fecha_vencimiento__lte=hoy
    ).select_related('producto').order_by('fecha_vencimiento')

    return {
        'alertas_stock': alertas_stock,
        'lotes_por_vencer': lotes_por_vencer,
        'lotes_vencidos': lotes_vencidos,
        'total_alertas': len(alertas_stock) + lotes_por_vencer.count() + lotes_vencidos.count()
    }


@transaction.atomic
def descontar_stock_fefo(producto: Producto, cantidad: int) -> List[Tuple[Lote, int]]:
    """
    Descuenta stock aplicando estrictamente el principio FEFO (First Expired, First Out).
    Usa select_for_update() para evitar condiciones de carrera entre usuarios concurrentes.
    Retorna una lista de tuplas (lote, cantidad_descontada).
    """
    if cantidad <= 0:
        raise ValueError("La cantidad a descontar debe ser mayor a 0.")

    hoy = timezone.localdate()
    # Bloquear filas para actualización ordenada por fecha de caducidad ascendente
    lotes = (
        producto.lotes
        .select_for_update()
        .filter(cantidad_actual__gt=0, fecha_vencimiento__gt=hoy)
        .order_by('fecha_vencimiento')
    )

    stock_disponible = sum(l.cantidad_actual for l in lotes)
    if stock_disponible < cantidad:
        raise StockInsuficienteException(producto.nombre, stock_disponible, cantidad)

    descuentos_realizados = []
    cantidad_restante = cantidad

    for lote in lotes:
        if cantidad_restante == 0:
            break
        a_descontar = min(lote.cantidad_actual, cantidad_restante)
        lote.descontar(a_descontar)
        descuentos_realizados.append((lote, a_descontar))
        cantidad_restante -= a_descontar

    return descuentos_realizados
