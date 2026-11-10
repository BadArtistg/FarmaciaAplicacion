from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.seguridad.models import Usuario, RolUsuario
from apps.inventario.models import Producto, Lote, CondicionVenta
from apps.recetas.models import Paciente, CupoPrograma, TipoCliente


class Command(BaseCommand):
    help = 'Carga los datos iniciales de práctica para la formación de Técnicos en Farmacia (INACAP Temuco).'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("=== Iniciando carga de datos de práctica ==="))

        # 1. Crear usuarios del prototipo
        usuarios_datos = [
            ('estudiante', 'Estudiante', 'Práctica', 'estudiante@inacapmail.cl', RolUsuario.ESTUDIANTE, False),
            ('cajero', 'Cajero', 'Simulado', 'cajero@inacapmail.cl', RolUsuario.CAJERO, False),
            ('docente', 'Docente', 'Supervisor', 'docente@inacapmail.cl', RolUsuario.DOCENTE, True),
            ('quimico', 'Químico', 'Farmacéutico', 'quimico@inacapmail.cl', RolUsuario.QUIMICO, True),
            ('admin', 'Administrador', 'Sistema', 'admin@inacapmail.cl', RolUsuario.ADMIN, True),
        ]

        for username, nombre, apellido, email, rol, exige_2fa in usuarios_datos:
            user, created = Usuario.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': nombre,
                    'last_name': apellido,
                    'email': email,
                    'rol': rol,
                    'dos_factores_activo': exige_2fa,
                    'is_staff': (rol == RolUsuario.ADMIN),
                    'is_superuser': (rol == RolUsuario.ADMIN),
                }
            )
            user.set_password('practica123')
            user.intentos_fallidos = 0
            user.bloqueado = False
            user.is_active = True
            user.rol = rol
            user.dos_factores_activo = exige_2fa
            user.save()

            estado_msg = "creado" if created else "actualizado"
            self.stdout.write(self.style.SUCCESS(f"  Usuario [{estado_msg}]: {username} | Rol: {rol} | Clave: practica123"))

        # 2. Crear medicamentos del prototipo
        hoy = timezone.localdate()

        productos_datos = [
            {
                'codigo': 'PA-500',
                'nombre': 'Paracetamol',
                'forma_farmaceutica': 'Comprimidos',
                'dosis': '500 mg',
                'condicion_venta': CondicionVenta.VENTA_DIRECTA,
                'es_controlado': False,
                'precio': 1290.00,
                'stock_minimo': 50,
                'lotes': [
                    ('PA-2201', hoy + timedelta(days=20), 40),   # Por vencer (<30d) -> Sale primero
                    ('PA-2305', hoy + timedelta(days=240), 120),
                ]
            },
            {
                'codigo': 'LO-50',
                'nombre': 'Losartán',
                'forma_farmaceutica': 'Comprimidos',
                'dosis': '50 mg',
                'condicion_venta': CondicionVenta.RECETA_SIMPLE,
                'es_controlado': False,
                'precio': 2490.00,
                'stock_minimo': 80,
                'lotes': [
                    ('LO-2188', hoy + timedelta(days=90), 60),    # Sale primero
                    ('LO-2310', hoy + timedelta(days=400), 200),
                ]
            },
            {
                'codigo': 'ME-850',
                'nombre': 'Metformina',
                'forma_farmaceutica': 'Comprimidos',
                'dosis': '850 mg',
                'condicion_venta': CondicionVenta.RECETA_SIMPLE,
                'es_controlado': False,
                'precio': 1990.00,
                'stock_minimo': 70,
                'lotes': [
                    ('ME-2190', hoy + timedelta(days=120), 90),   # Sale primero
                    ('ME-2299', hoy + timedelta(days=360), 150),
                ]
            },
            {
                'codigo': 'AM-500',
                'nombre': 'Amoxicilina',
                'forma_farmaceutica': 'Cápsulas',
                'dosis': '500 mg',
                'condicion_venta': CondicionVenta.RECETA_SIMPLE,
                'es_controlado': False,
                'precio': 3990.00,
                'stock_minimo': 30,
                'lotes': [
                    ('AM-2210', hoy + timedelta(days=70), 25),    # Sale primero
                    ('AM-2308', hoy + timedelta(days=500), 60),
                ]
            },
            {
                'codigo': 'CL-2',
                'nombre': 'Clonazepam',
                'forma_farmaceutica': 'Comprimidos',
                'dosis': '2 mg',
                'condicion_venta': CondicionVenta.RECETA_RETENIDA,
                'es_controlado': True,  # Controlado: requiere químico
                'precio': 4500.00,
                'stock_minimo': 20,
                'lotes': [
                    ('CL-2250', hoy + timedelta(days=180), 30),
                ]
            },
            {
                'codigo': 'IB-400',
                'nombre': 'Ibuprofeno',
                'forma_farmaceutica': 'Comprimidos',
                'dosis': '400 mg',
                'condicion_venta': CondicionVenta.VENTA_DIRECTA,
                'es_controlado': False,
                'precio': 1100.00,
                'stock_minimo': 50,
                'lotes': [
                    ('IB-101', hoy + timedelta(days=10), 8),      # Crítico en stock (<50) y por vencer
                ]
            }
        ]

        for p_data in productos_datos:
            producto, _ = Producto.objects.update_or_create(
                codigo=p_data['codigo'],
                defaults={
                    'nombre': p_data['nombre'],
                    'forma_farmaceutica': p_data['forma_farmaceutica'],
                    'dosis': p_data['dosis'],
                    'condicion_venta': p_data['condicion_venta'],
                    'es_controlado': p_data['es_controlado'],
                    'precio': p_data['precio'],
                    'stock_minimo': p_data['stock_minimo'],
                }
            )

            for lote_cod, fecha_venc, cant in p_data['lotes']:
                Lote.objects.update_or_create(
                    producto=producto,
                    codigo=lote_cod,
                    defaults={
                        'fecha_vencimiento': fecha_venc,
                        'cantidad_inicial': cant,
                        'cantidad_actual': cant,
                    }
                )
            self.stdout.write(self.style.SUCCESS(f"  Producto y lotes cargados: {producto.nombre} ({producto.stock_total} u.)"))

        # 3. Paciente ficticio para simulación
        paciente, _ = Paciente.objects.get_or_create(
            rut_ficticio='12.345.678-9',
            defaults={
                'nombre': 'Rosa Muñoz (Ficticia)',
                'tipo_cliente': TipoCliente.PROGRAMA_PUBLICO,
                'telefono': '+56 9 8765 4321'
            }
        )

        CupoPrograma.objects.get_or_create(
            paciente=paciente,
            programa='Programa Crónicos CESFAM',
            defaults={
                'cantidad_mensual': 60,
                'cantidad_usada': 0,
                'vigente_hasta': hoy + timedelta(days=365)
            }
        )
        self.stdout.write(self.style.SUCCESS(f"  Paciente de práctica cargado: {paciente.nombre} (Cupo 60 u.)"))

        self.stdout.write(self.style.SUCCESS("\n¡Datos de práctica cargados con éxito!"))
