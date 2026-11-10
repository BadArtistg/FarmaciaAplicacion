"""
Inversión de Dependencias: Interfaz y Pasarela Simulada de Pago (Sección 2.2 y 8 del Informe de Diseño).
Permite desacoplar el cobro de una pasarela real o simulada para la práctica de los estudiantes.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
import uuid


@dataclass
class ResultadoPago:
    aprobado: bool
    referencia: str
    mensaje: str
    datos_transaccion: dict


class PasarelaPago(ABC):
    @abstractmethod
    def cobrar(self, monto: float, metadata: dict = None) -> ResultadoPago:
        """Contrato abstracto para procesamiento de cobro."""
        pass


class PasarelaSimulada(PasarelaPago):
    """
    Pasarela ficticia para el laboratorio de Técnico en Farmacia.
    Simula aprobaciones inmediatas con generación de folio y registro auditable.
    """

    def cobrar(self, monto: float, metadata: dict = None) -> ResultadoPago:
        if monto < 0:
            return ResultadoPago(
                aprobado=False,
                referencia="ERROR-MONTO",
                mensaje="El monto a cobrar no puede ser negativo.",
                datos_transaccion={"error": "monto_invalido"}
            )

        ref_id = f"SIM-{uuid.uuid4().hex[:8].upper()}"
        return ResultadoPago(
            aprobado=True,
            referencia=ref_id,
            mensaje="Pago simulado aprobado exitosamente en entorno de práctica INACAP.",
            datos_transaccion={
                "pasarela": "PasarelaSimulada",
                "referencia": ref_id,
                "monto": str(monto),
                "modo": "PRACTICA_DOCENTE",
                "validez": "SIN_VALIDEZ_TRIBUTARIA",
                "metadata": metadata or {}
            }
        )
