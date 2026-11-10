import pytest
from django.urls import reverse
from django.core.exceptions import ValidationError
from apps.seguridad.models import Usuario, RolUsuario, AuditoriaEvento

@pytest.mark.django_db
class TestSeguridadYAutenticacion:

    def test_bloqueo_cuenta_tras_5_intentos_fallidos_caso_ps01(self, client):
        """
        Caso PS-01: Ingresar 5 contraseñas incorrectas seguidas.
        Resultado esperado: Cuenta bloqueada y evento registrado en la bitácora.
        """
        user = Usuario.objects.create_user(
            username='estudiante_test',
            password='Password1234!',
            rol=RolUsuario.ESTUDIANTE
        )

        login_url = reverse('seguridad:login')

        # Realizar 5 intentos con contraseña errónea
        for i in range(5):
            response = client.post(login_url, {
                'username': 'estudiante_test',
                'password': 'PasswordIncorrecta999'
            })
            assert response.status_code == 200

        user.refresh_from_db()
        assert user.bloqueado is True
        assert user.is_active is False
        assert user.intentos_fallidos == 5

        # Verificar evento en auditoría
        evento_bloqueo = AuditoriaEvento.objects.filter(
            accion='CUENTA_BLOQUEADA_POR_INTENTOS',
            usuario=user
        ).first()
        assert evento_bloqueo is not None
        assert evento_bloqueo.detalle['intentos'] == 5

    def test_acceso_restringido_estudiante_caso_ps02(self, client):
        """
        Caso PS-02: Un estudiante intenta abrir la URL de Gestión de Usuarios.
        Resultado esperado: Respuesta 403 Forbidden y evento registrado en auditoría.
        """
        estudiante = Usuario.objects.create_user(
            username='estudiante_rbac',
            password='Password1234!',
            rol=RolUsuario.ESTUDIANTE
        )
        client.force_login(estudiante)

        url_usuarios = reverse('seguridad:usuario_list')
        response = client.get(url_usuarios)

        assert response.status_code == 403

        # Verificar registro del intento en la bitácora inmutable
        evento_denegado = AuditoriaEvento.objects.filter(
            accion='ACCESO_DENEGADO_ROL',
            usuario=estudiante
        ).first()
        assert evento_denegado is not None
        assert evento_denegado.detalle['rol_usuario'] == RolUsuario.ESTUDIANTE

    def test_login_con_segundo_factor_obligatorio_docente(self, client):
        """
        CU-05: El docente tiene 2FA obligatorio. Debe ser redirigido a la verificación de 2FA.
        """
        docente = Usuario.objects.create_user(
            username='docente_test',
            password='Password1234!',
            rol=RolUsuario.DOCENTE,
            dos_factores_activo=True
        )

        login_url = reverse('seguridad:login')
        response = client.post(login_url, {
            'username': 'docente_test',
            'password': 'Password1234!'
        })

        assert response.status_code == 302
        assert response.url == reverse('seguridad:two_factor')

        # Verificar segundo factor con código de práctica '123456'
        two_fa_url = reverse('seguridad:two_factor')
        res_2fa = client.post(two_fa_url, {'codigo': '123456'})
        assert res_2fa.status_code == 302
        assert res_2fa.url == reverse('inventario:dashboard')

    def test_auditoria_es_inmutable_no_permite_modificacion_ni_borrado(self):
        """
        Garantía de integridad de la sección 5.2: la tabla auditoria_eventos
        no admite actualizar ni borrar registros.
        """
        evento = AuditoriaEvento.objects.create(
            accion='TEST_EVENTO',
            entidad='Prueba',
            usuario_str='admin_test',
            detalle={'test': True}
        )

        # Intentar modificar el registro debe lanzar ValidationError
        evento.accion = 'EVENTO_ALTERADO'
        with pytest.raises(ValidationError):
            evento.save()

        # Intentar eliminar el registro debe lanzar ValidationError
        with pytest.raises(ValidationError):
            evento.delete()
