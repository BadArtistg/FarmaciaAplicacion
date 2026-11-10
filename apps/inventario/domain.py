"""
Reglas puras del Dominio de Inventario.
Implementa el principio de encapsulamiento y el algoritmo FEFO (First Expired, First Out).
"""
from datetime import date
from typing import List, Tuple, Any


class StockInsuficienteException(Exception):
    """Lanzada cuando la cantidad solicitada supera el stock disponible."""
    def __init__(self, producto_nombre: str, disponible: int, solicitado: int):
        self.producto_nombre = producto_nombre
        self.disponible = disponible
        self.solicitado = solicitado
        super().__init__(
            f"Stock insuficiente para '{producto_nombre}'. Disponible: {disponible}, Solicitado: {solicitado}"
        )


class LoteVencidoException(Exception):
    """Lanzada cuando se intenta ingresar o utilizar un lote ya vencido."""
    def __init__(self, codigo_lote: str, fecha_vencimiento: date):
        self.codigo_lote = codigo_lote
        self.fecha_vencimiento = fecha_vencimiento
        super().__init__(
            f"El lote '{codigo_lote}' tiene fecha de vencimiento {fecha_vencimiento} y se encuentra vencido. No se permite el ingreso."
        )


def validar_fecha_vencimiento_ingreso(fecha_venc: date, hoy: date = None) -> None:
    """Regla de integridad: no se admiten lotes vencidos en el ingreso (Sección 5.2)."""
    if hoy is None:
        hoy = date.today()
    if fecha_venc <= hoy:
        raise LoteVencidoException("NUEVO", fecha_venc)


def calcular_orden_fefo(lotes: List[Any], hoy: date = None) -> List[Any]:
    """
    Ordena una lista de lotes por FEFO (First Expired, First Out):
    Prioriza los lotes no vencidos con stock > 0 por fecha de vencimiento ascendente.
    """
    if hoy is None:
        hoy = date.today()

    lotes_vigentes = [l for l in lotes if l.fecha_vencimiento > hoy and l.cantidad_actual > 0]
    return sorted(lotes_vigentes, key=lambda l: l.fecha_vencimiento)
