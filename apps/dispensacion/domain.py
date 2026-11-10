"""
Patrón Strategy para los flujos de dispensación (Sección 2.2 y 8 del Informe de Diseño).
Permite extender y procesar FlujoGratuito, FlujoPago y FlujoMixto de forma desacoplada.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict


class FlujoDespacho(ABC):
    """Interfaz base Strategy para la ejecución de un despacho."""

    @abstractmethod
    def ejecutar(self, receta: Any, usuario: Any, datos_extra: Dict = None) -> Any:
        pass


class FlujoGratuito(FlujoDespacho):
    """Atención de recetas del programa público (100% cobertura con cargo al cupo)."""

    def ejecutar(self, receta: Any, usuario: Any, datos_extra: Dict = None) -> Any:
        # Implementación completa en Sprint 2
        return {"tipo": "GRATUITO", "receta_id": getattr(receta, 'id', None)}


class FlujoPago(FlujoDespacho):
    """Atención de recetas particulares o venta directa con cobro."""

    def ejecutar(self, receta: Any, usuario: Any, datos_extra: Dict = None) -> Any:
        # Implementación completa en Sprint 3
        return {"tipo": "PAGO", "receta_id": getattr(receta, 'id', None)}


class FlujoMixto(FlujoDespacho):
    """
    Atención de receta con ítems cubiertos por cupo de programa
    y excedentes derivados al flujo de pago.
    """

    def ejecutar(self, receta: Any, usuario: Any, datos_extra: Dict = None) -> Any:
        # Implementación completa en Sprint 3
        return {"tipo": "MIXTO", "receta_id": getattr(receta, 'id', None)}
