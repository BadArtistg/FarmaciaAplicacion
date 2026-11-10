# Sistema Web de Farmacia Mixta · Formación de Técnicos en Farmacia (INACAP Temuco)

Plataforma web académica orientada a la simulación y práctica realista de los estudiantes de la carrera de **Técnico en Farmacia de INACAP Temuco**, permitiendo ejercitar el control de inventarios, dispensación asistencial bajo normativa chilena (FEFO, medicamentos controlados y programas GES/crónicos) y cobro en farmacia mixta (pública y privada).

---

## Estado del Proyecto: Sprint 1 Completado & Base Escalable

El proyecto implementa la arquitectura y los componentes completos hasta el **Sprint 1 (Logueo Seguro e Inventario)**, dejando la estructura modular preparada para los siguientes sprints:

- **Sprint 1 (Completado):** Autenticación segura con bloqueo por fuerza bruta tras 5 intentos (PS-01), Segundo Factor (2FA/TOTP) para roles con privilegio, control de acceso basado en roles (RBAC), auditoría inmutable de eventos, catálogo de medicamentos e inventario por lotes con algoritmo sanitario **FEFO (First Expired, First Out)**, etiqueta *"Sale primero"*, rechazo de lotes vencidos (PF-03) y panel de alertas de stock crítico y vencimientos.
- **Sprint 2 (Preparado en `apps/recetas` y `apps/dispensacion`):** Registro de recetas, pacientes ficticios, consumo de cupo mensual de programas de salud, autorización de medicamentos controlados por Químico Farmacéutico y dispensación gratuita.
- **Sprint 3 (Preparado en `apps/caja` y `apps/dispensacion`):** Patrón Strategy (`FlujoGratuito`, `FlujoPago`, `FlujoMixto`), Inversión de Dependencias con pasarela de pago simulada (`PasarelaSimulada`) y emisión de comprobante de práctica con la leyenda *"Simulación – sin validez tributaria"*.

---

##  Arquitectura 4+1 (Kruchten)

1. **Vista de Escenarios (Casos de Uso):**
   - **CU-01 / CU-02:** Registro de producto y lote con validación de caducidad (`vencimiento > hoy`).
   - **CU-03:** Consulta de inventario en orden FEFO con identificación del lote que sale primero.
   - **CU-04:** Alertas de stock crítico y lotes por vencer en &le; 30 días.
   - **CU-05:** Iniciar sesión seguro con bloqueo a los 5 intentos y 2FA obligatorio para Docente, Químico y Administrador.
   - **CU-06:** Bitácora inmutable de auditoría para supervisión y evaluación docente.
2. **Vista Lógica (Dominio y Principios POO):**
   - **Encapsulamiento:** El stock de un lote únicamente se modifica mediante el método de dominio `lote.descontar(cantidad)`.
   - **Patrón Strategy:** Interfaz abstracta `FlujoDespacho` con implementaciones `FlujoGratuito`, `FlujoPago` y `FlujoMixto` en `apps/dispensacion/domain.py`.
   - **Inversión de Dependencias (DIP):** Interfaz `PasarelaPago` desacoplada en `apps/caja/pasarela.py`, implementada por `PasarelaSimulada`.
3. **Vista de Desarrollo (Monolito Modular en Capas):**
   ```text
   farmacia/
   ├── config/                  # Configuración central (settings, urls, wsgi)
   ├── apps/
   │   ├── seguridad/           # Usuarios (AbstractUser), RBAC, 2FA, Bitácora inmutable
   │   ├── inventario/          # Productos, Lotes, FEFO, Alertas de stock
   │   ├── recetas/             # Pacientes, Cupos de Programa, Recetas (Sprint 2)
   │   ├── dispensacion/        # Despachos, Detalles y Strategy Flujos (Sprint 2 & 3)
   │   └── caja/                # Pagos, Pasarela Simulada, Comprobantes (Sprint 3)
   ├── templates/               # Plantillas responsivas (400px móvil) con tokens accesibles
   ├── static/                  # CSS y JS con soporte de semáforos verde/ámbar/rojo con texto
   └── tests/                   # Suite automatizada con pytest-django
   ```
4. **Vista de Procesos (BPMN):**
   - Flujo de atención con validación de cuotas y autorización de controlados.
   - Flujo de login seguro con bloqueo tras 5 intentos y validación TOTP.
5. **Vista Física (Despliegue Contenedorizado):**
   - `docker-compose.yml` orquestando: Web/App (Django + Gunicorn), Base de Datos (PostgreSQL 16) y Caché (Redis).

---

## Matriz de Roles y Privilegios (Sección 6.1)

| Rol | Consultar Inventario y Alertas | Registrar Productos y Lotes | Registrar Receta y Despachar | Autorizar Controlado | Cobrar y Emitir Comprobante | Ver Registro de Actividad | Gestionar Usuarios / 2FA |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Estudiante** | Sí | Sí | Sí *(S2)* | No | No | No | No |
| **Cajero** | No | No | No | No | Sí *(S3)* | No | No |
| **Docente** | Sí | Sí | Sí *(S2)* | No | No | Sí | No |
| **Químico** | Sí | No | Sí *(S2)* | Sí *(S2)* | No | No | No |
| **Admin** | Sí | Sí | No | No | No | Sí | Sí |

---

## Credenciales de Prueba Precargadas

| Usuario | Rol | Contraseña | 2FA (TOTP) |
| :--- | :--- | :--- | :--- |
| `estudiante` | Estudiante Técnico en Farmacia | `practica123` | *No requerido* |
| `cajero` | Cajero Simulado | `practica123` | *No requerido* |
| `docente` | Docente a Cargo / Supervisor | `practica123` | Obligatorio: `123456` |
| `quimico` | Químico Farmacéutico | `practica123` | Obligatorio: `123456` |
| `admin` | Administrador del Sistema | `practica123` | Obligatorio: `123456` |

---

## Puesta en Marcha

### Opción 1: Ejecución Local

1. **Activar el entorno virtual:**
   - En Windows PowerShell:
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
2. **Aplicar migraciones:**
   ```powershell
   python manage.py migrate
   ```
3. **Cargar datos ficticios de práctica:**
   ```powershell
   python manage.py cargar_datos_practica
   ```
4. **Ejecutar servidor de desarrollo:**
   ```powershell
   python manage.py runserver
   ```
   Acceder en el navegador a: `http://127.0.0.1:8000`

### Opción 2: Despliegue con Docker Compose (PostgreSQL + Redis)

```bash
docker compose up --build -d
docker compose exec app python manage.py migrate
docker compose exec app python manage.py cargar_datos_practica
```

---

## Pruebas Automatizadas

El proyecto incluye pruebas que validan los casos representativos del plan de pruebas:
- **PS-01:** Bloqueo de cuenta tras 5 contraseñas incorrectas seguidas y registro en auditoría.
- **PS-02:** Intento de acceso no autorizado por un estudiante (código HTTP 403 y registro en bitácora).
- **PF-03:** Rechazo con mensaje claro al intentar ingresar un lote con fecha vencida.
- **FEFO:** Ordenamiento sanitario First Expired, First Out y descuento atómico con `select_for_update()`.
- **Inmutabilidad:** Verificación de rechazo a modificaciones o borrados en la bitácora de auditoría.

Para ejecutar la suite de pruebas:
```powershell
pytest
```
Resultado: **8 pruebas pasadas al 100%**.
