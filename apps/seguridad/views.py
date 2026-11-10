from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.conf import settings

from .models import Usuario, RolUsuario, AuditoriaEvento
from .forms import LoginForm, TwoFactorForm, UsuarioForm
from .services import registrar_auditoria, validar_codigo_totp
from .decorators import requiere_roles


def login_view(request):
    if request.user.is_authenticated:
        return redirect('inventario:dashboard')

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data['username'].strip()
        password = form.cleaned_data['password']

        # Verificar si el usuario existe para gestión de bloqueo
        try:
            usuario_existente = Usuario.objects.get(username=username)
        except Usuario.DoesNotExist:
            usuario_existente = None

        if usuario_existente and usuario_existente.bloqueado:
            registrar_auditoria(
                accion='INTENTO_LOGIN_CUENTA_BLOQUEADA',
                entidad='Autenticacion',
                usuario=usuario_existente,
                detalle={'username': username, 'motivo': 'Cuenta previamente bloqueada por 5 intentos'},
                request=request
            )
            messages.error(
                request,
                'Esta cuenta se encuentra bloqueada por exceder 5 intentos fallidos. Contacte al Administrador.'
            )
            return render(request, 'seguridad/login.html', {'form': form})

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if not user.is_active or user.bloqueado:
                messages.error(request, 'La cuenta está inactiva o bloqueada.')
                return render(request, 'seguridad/login.html', {'form': form})

            # Caso con Segundo Factor obligatorio o activo
            if user.exige_2fa:
                request.session['pre_2fa_user_id'] = user.id
                registrar_auditoria(
                    accion='SOLICITUD_SEGUNDO_FACTOR',
                    entidad='Autenticacion',
                    usuario=user,
                    detalle={'rol': user.rol, 'ip': request.META.get('REMOTE_ADDR')},
                    request=request
                )
                return redirect('seguridad:two_factor')

            # Login directo para roles sin 2FA (Estudiante, Cajero)
            user.restablecer_intentos()
            login(request, user)
            registrar_auditoria(
                accion='INICIO_SESION_EXITOSO',
                entidad='Autenticacion',
                usuario=user,
                detalle={'rol': user.rol},
                request=request
            )
            messages.success(request, f'Bienvenido(a), {user.get_full_name() or user.username} ({user.get_rol_display()}).')
            return redirect('inventario:dashboard')
        else:
            # Credenciales inválidas: procesar intentos fallidos (Caso PS-01)
            if usuario_existente:
                se_bloqueo = usuario_existente.registrar_intento_fallido()
                if se_bloqueo:
                    registrar_auditoria(
                        accion='CUENTA_BLOQUEADA_POR_INTENTOS',
                        entidad='Autenticacion',
                        usuario=usuario_existente,
                        detalle={
                            'intentos': usuario_existente.intentos_fallidos,
                            'max_permitido': settings.MAX_INTENTOS_LOGIN
                        },
                        request=request
                    )
                    messages.error(
                        request,
                        '¡Cuenta bloqueada! Ha superado el límite de 5 intentos fallidos consecutivos.'
                    )
                else:
                    intentos_restantes = settings.MAX_INTENTOS_LOGIN - usuario_existente.intentos_fallidos
                    registrar_auditoria(
                        accion='INTENTO_FALLIDO_CONTRASENA',
                        entidad='Autenticacion',
                        usuario=usuario_existente,
                        detalle={
                            'intento_numero': usuario_existente.intentos_fallidos,
                            'intentos_restantes': intentos_restantes
                        },
                        request=request
                    )
                    messages.warning(
                        request,
                        f'Contraseña incorrecta. Le quedan {intentos_restantes} intento(s) antes del bloqueo.'
                    )
            else:
                registrar_auditoria(
                    accion='INTENTO_LOGIN_USUARIO_INEXISTENTE',
                    entidad='Autenticacion',
                    usuario=username,
                    detalle={'username_ingresado': username},
                    request=request
                )
                messages.error(request, 'Usuario o contraseña inválidos.')

    return render(request, 'seguridad/login.html', {'form': form})


def two_factor_verify_view(request):
    user_id = request.session.get('pre_2fa_user_id')
    if not user_id:
        return redirect('seguridad:login')

    usuario = get_object_or_404(Usuario, id=user_id)
    form = TwoFactorForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        codigo = form.cleaned_data['codigo']
        if validar_codigo_totp(usuario, codigo):
            usuario.restablecer_intentos()
            login(request, usuario)
            del request.session['pre_2fa_user_id']
            registrar_auditoria(
                accion='INICIO_SESION_2FA_EXITOSO',
                entidad='Autenticacion',
                usuario=usuario,
                detalle={'rol': usuario.rol, '2fa_metodo': 'TOTP'},
                request=request
            )
            messages.success(request, f'Sesión iniciada con 2FA exitosamente ({usuario.get_rol_display()}).')
            return redirect('inventario:dashboard')
        else:
            registrar_auditoria(
                accion='CODIGO_2FA_INVALIDO',
                entidad='Autenticacion',
                usuario=usuario,
                detalle={'codigo_probado': codigo},
                request=request
            )
            messages.error(request, 'Código de verificación incorrecto. Intente nuevamente.')

    return render(request, 'seguridad/two_factor.html', {
        'form': form,
        'usuario': usuario,
        'modo_practica': getattr(settings, 'MODO_PRACTICA', True),
        'codigo_practica': getattr(settings, 'CODIGO_2FA_PRACTICA', '123456')
    })


def logout_view(request):
    if request.user.is_authenticated:
        registrar_auditoria(
            accion='CIERRE_SESION',
            entidad='Autenticacion',
            usuario=request.user,
            request=request
        )
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('seguridad:login')


@requiere_roles(RolUsuario.ADMIN, RolUsuario.DOCENTE)
def usuario_list_view(request):
    """Listado y gestión de usuarios del sistema."""
    usuarios = Usuario.objects.all().order_by('username')
    return render(request, 'seguridad/usuarios_list.html', {'usuarios': usuarios})


@requiere_roles(RolUsuario.ADMIN)
def usuario_create_view(request):
    form = UsuarioForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        nuevo_usuario = form.save()
        registrar_auditoria(
            accion='USUARIO_CREADO',
            entidad='Usuario',
            usuario=request.user,
            detalle={'nuevo_username': nuevo_usuario.username, 'rol': nuevo_usuario.rol},
            request=request
        )
        messages.success(request, f'Usuario {nuevo_usuario.username} creado exitosamente.')
        return redirect('seguridad:usuario_list')
    return render(request, 'seguridad/usuario_form.html', {'form': form, 'titulo': 'Nuevo Usuario'})


@requiere_roles(RolUsuario.ADMIN)
def usuario_update_view(request, pk):
    usuario_obj = get_object_or_404(Usuario, pk=pk)
    form = UsuarioForm(request.POST or None, instance=usuario_obj)
    if request.method == 'POST' and form.is_valid():
        usuario_actualizado = form.save()
        registrar_auditoria(
            accion='USUARIO_MODIFICADO',
            entidad='Usuario',
            usuario=request.user,
            detalle={'username_modificado': usuario_actualizado.username, 'rol': usuario_actualizado.rol},
            request=request
        )
        messages.success(request, f'Usuario {usuario_actualizado.username} actualizado.')
        return redirect('seguridad:usuario_list')
    return render(request, 'seguridad/usuario_form.html', {
        'form': form,
        'titulo': f'Editar Usuario: {usuario_obj.username}',
        'usuario_obj': usuario_obj
    })


@requiere_roles(RolUsuario.ADMIN)
@require_http_methods(["POST"])
def usuario_desbloquear_view(request, pk):
    usuario_obj = get_object_or_404(Usuario, pk=pk)
    usuario_obj.desbloquear()
    registrar_auditoria(
        accion='CUENTA_DESBLOQUEADA_POR_ADMIN',
        entidad='Usuario',
        usuario=request.user,
        detalle={'usuario_desbloqueado': usuario_obj.username},
        request=request
    )
    messages.success(request, f'La cuenta {usuario_obj.username} ha sido desbloqueada satisfactoriamente.')
    return redirect('seguridad:usuario_list')


@requiere_roles(RolUsuario.ADMIN, RolUsuario.DOCENTE)
def auditoria_list_view(request):
    """
    CU-06 / Registro de actividad inmutable.
    Permite supervisión por parte del Administrador y Docente.
    """
    query = request.GET.get('q', '').strip()
    accion_filtro = request.GET.get('accion', '').strip()
    eventos = AuditoriaEvento.objects.all()

    if query:
        eventos = eventos.filter(
            Q(usuario_str__icontains=query) |
            Q(entidad__icontains=query) |
            Q(accion__icontains=query)
        )
    if accion_filtro:
        eventos = eventos.filter(accion=accion_filtro)

    eventos = eventos[:200]  # Limitar a los 200 eventos más recientes
    acciones_disponibles = AuditoriaEvento.objects.values_list('accion', flat=True).distinct()

    return render(request, 'seguridad/auditoria.html', {
        'eventos': eventos,
        'query': query,
        'accion_filtro': accion_filtro,
        'acciones_disponibles': acciones_disponibles
    })
