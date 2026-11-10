from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from django.contrib import messages
from .domain import tiene_capacidad
from .services import registrar_auditoria


def requiere_roles(*roles_permitidos):
    """
    Decorador que verifica que el usuario autenticado pertenezca a uno de los roles permitidos.
    Si no tiene acceso, devuelve HTTP 403 y registra un evento de auditoría (Caso PS-02).
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('seguridad:login')

            if request.user.rol not in roles_permitidos:
                # Registrar intento de acceso no autorizado en la bitácora
                registrar_auditoria(
                    accion='ACCESO_DENEGADO_ROL',
                    entidad='Seguridad',
                    usuario=request.user,
                    detalle={
                        'path': request.path,
                        'rol_usuario': request.user.rol,
                        'roles_requeridos': list(roles_permitidos),
                        'motivo': 'Control de acceso basado en roles (RBAC)'
                    },
                    request=request
                )
                return render(
                    request,
                    'errors/403.html',
                    {
                        'mensaje': 'No tienes permisos para acceder a este módulo según tu rol asignado.',
                        'rol_actual': request.user.get_rol_display(),
                    },
                    status=403
                )
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def requiere_capacidad(capacidad: str):
    """
    Decorador basado en capacidades del dominio según la matriz de la sección 6.1.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('seguridad:login')

            if not tiene_capacidad(request.user.rol, capacidad):
                registrar_auditoria(
                    accion='ACCESO_DENEGADO_CAPACIDAD',
                    entidad='Seguridad',
                    usuario=request.user,
                    detalle={
                        'path': request.path,
                        'capacidad_requerida': capacidad,
                        'rol_usuario': request.user.rol
                    },
                    request=request
                )
                return render(
                    request,
                    'errors/403.html',
                    {
                        'mensaje': f'Acceso restringido: se requiere la capacidad "{capacidad}".',
                        'rol_actual': request.user.get_rol_display(),
                    },
                    status=403
                )
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
