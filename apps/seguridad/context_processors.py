from .models import RolUsuario
from .domain import CAPACIDADES_POR_ROL

def auth_roles(request):
    """
    Context processor que expone flags de roles y permisos a todas las plantillas.
    Permite ocultar o mostrar opciones de menú según el principio de mínimo privilegio.
    (La seguridad real se sigue comprobando en el servidor en cada vista).
    """
    if not request.user.is_authenticated:
        return {
            'rol_usuario': None,
            'es_estudiante': False,
            'es_cajero': False,
            'es_docente': False,
            'es_quimico': False,
            'es_admin': False,
            'capacidades_usuario': set(),
        }

    rol = request.user.rol
    return {
        'rol_usuario': rol,
        'rol_usuario_display': request.user.get_rol_display(),
        'es_estudiante': rol == RolUsuario.ESTUDIANTE,
        'es_cajero': rol == RolUsuario.CAJERO,
        'es_docente': rol == RolUsuario.DOCENTE,
        'es_quimico': rol == RolUsuario.QUIMICO,
        'es_admin': rol == RolUsuario.ADMIN,
        'capacidades_usuario': CAPACIDADES_POR_ROL.get(rol, set()),
    }
