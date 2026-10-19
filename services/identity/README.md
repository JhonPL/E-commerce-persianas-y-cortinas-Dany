# Identity Service

Servicio Django independiente para autenticación, roles y perfiles de cliente.
Conserva las rutas HTTP existentes; el backend monolítico funciona como proxy
para mantener sin cambios las URLs del frontend.

## Configuración

Este servicio requiere su propia base PostgreSQL. Copia `.env.example` a `.env`
y configura los valores antes de iniciar. `DJANGO_SECRET_KEY` debe ser
exactamente el mismo valor que `SECRET_KEY` del backend existente: ambos
servicios emiten y validan los mismos JWT. Configura también el mismo
`INTERNAL_SERVICE_TOKEN` en el backend y los demás servicios. Google OAuth usa
el mismo cliente OAuth y las mismas URIs permitidas que el frontend.

Instala las dependencias, aplica migraciones y ejecuta el servidor:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 127.0.0.1:8004
```

El backend se mantiene en el puerto 8000 y reenvía `/api/v1/auth/` y
`/api/v1/admin/usuarios/` a este servicio. Los servicios de catálogo, carrito y
pedidos validan JWT directamente mediante `/api/v1/auth/me/`.

## Transferencia de datos

Aplica primero las migraciones en la base vacía del servicio. Antes del corte,
haz una copia de seguridad verificable del monolito y exporta desde la carpeta
`backend` a una ubicación local protegida que no esté dentro del repositorio:

```powershell
python manage.py export_identity_data --file C:\secure-transfer\identity.json
```

Con la nueva base del servicio lista, importa el archivo:

```powershell
python manage.py import_identity_data C:\secure-transfer\identity.json
```

La transferencia conserva los IDs de roles, usuarios y perfiles, los hashes de
contraseña existentes, proveedores OAuth y banderas administrativas. Conservar
IDs es necesario porque los servicios de carrito y pedidos referencian usuarios
por ID. La importación solo se permite en una base vacía. No abras, imprimas,
envíes ni subas el archivo: contiene hashes de contraseñas y datos personales.
Verifica conteos e inicio de sesión antes de cambiar el tráfico; elimina el
archivo protegido después de validar y conserva la copia de seguridad según tu
política de recuperación. En Windows, guárdalo en una carpeta cifrada o con ACL
de acceso restringido: los permisos POSIX de la exportación no sustituyen las
ACL de Windows.

No se ha ejecutado una exportación ni importación de datos reales en este corte.

## Compatibilidad legacy y límites

- Las rutas de autenticación y administración de usuarios mantienen sus
  respuestas existentes y se conservan detrás del proxy del backend.
- `/api/internal/identity/resumen/` solo acepta el token interno compartido; lo
  usa el dashboard del backend para obtener métricas de clientes.
- Los modelos y tablas de usuario del monolito se mantienen para la
  compatibilidad de migraciones y dependencias legacy. El registro y perfil
  activos se escriben en este servicio y no replican cambios al monolito.
- Pagos permanece sin cambios en el monolito. Sus relaciones y validación
  locales siguen dependiendo de las tablas heredadas; por tanto, no se debe
  considerar que pagos funciona con usuarios creados únicamente en este
  servicio. La transferencia conserva usuarios existentes, pero no sincroniza
  altas o cambios posteriores.
- El comando legacy `seed_demo` sigue creando usuarios en el monolito y no debe
  usarse después del corte sin adaptarlo en una etapa posterior.

## Verificación

```powershell
python manage.py test --settings=auth_service.test_settings
```

La documentación OpenAPI está disponible en `/api/docs/` y `/api/schema/`.
