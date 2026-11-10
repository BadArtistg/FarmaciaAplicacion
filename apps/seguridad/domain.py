"""
Reglas puras del dominio de Seguridad y Control de Acceso (RBAC).
Matriz de permisos definida en la Sección 6.1 del Informe de Diseño (Etapa II).
"""
from typing import Set
from .models import RolUsuario


# Matriz de roles y capacidades según el documento de diseño
CAPACIDADES_POR_ROL = {
    RolUsuario.ESTUDIANTE: {
        'consultar_inventario',
        'registrar_productos_y_lotes',
        'registrar_receta_y_despachar',
    },
    RolUsuario.CAJERO: {
        'cobrar_y_emitir_comprobante',
    },
    RolUsuario.DOCENTE: {
        'consultar_inventario',
        'registrar_productos_y_lotes',
        'registrar_receta_y_despachar',
        'ver_registro_actividad',
    },
    RolUsuario.QUIMICO: {
        'consultar_inventario',
        'registrar_receta_y_despachar',
        'autorizar_medicamento_controlado',
    },
    RolUsuario.ADMIN: {
        'consultar_inventario',
        'registrar_productos_y_lotes',
        'ver_registro_actividad',
        'gestionar_usuarios_roles_2fa',
    },
}


def tiene_capacidad(rol: str, capacidad: str) -> bool:
    """Verifica si un rol posee una capacidad del sistema según la matriz RBAC."""
    capacidades = CAPACIDADES_POR_ROL.get(rol, set())
    return capacidad in capacidades


def puede_consultar_inventario(rol: str) -> bool:
    return tiene_capacidad(rol, 'consultar_inventario')


def puede_gestionar_inventario(rol: str) -> bool:
    return tiene_capacidad(rol, 'registrar_productos_y_lotes')


def puede_ver_auditoria(rol: str) -> bool:
    return tiene_capacidad(rol, 'ver_registro_actividad')


def puede_gestionar_usuarios(rol: str) -> bool:
    return tiene_capacidad(rol, 'gestionar_usuarios_roles_2fa')
