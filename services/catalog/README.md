# Catalog Service

Servicio Django dueño de productos, categorías e imágenes. El gateway publica
las rutas consumidas por el frontend; los demás servicios consultan el catálogo
mediante endpoints internos autenticados.

## Configuración y desarrollo

Configura `.env` con una base PostgreSQL independiente, Cloudinary (si se usa
carga de imágenes) y el token interno compartido. `AUTH_SERVICE_URL` debe
apuntar a `auth-service` para validar sesiones administrativas.

Desde la raíz del repositorio, el entorno Python compartido es `.venv`. Para
iniciar manualmente:

```powershell
..\..\.venv\Scripts\python.exe manage.py migrate
..\..\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8001
```

En el uso normal, `.\run-local.ps1` inicia el catálogo junto con los demás
servicios y el gateway.

## Integraciones

- Identidad valida usuarios y roles; el catálogo no duplica usuarios.
- Carrito y pedidos consultan productos mediante la API interna protegida por
  `INTERNAL_SERVICE_TOKEN`.
- Antes de borrar un producto, el gateway comprueba referencias en pedidos y
  elimina del carrito los artículos asociados.
- Los productos de demostración se pueden crear con
  `manage.py seed_demo_catalog`; el comando solo siembra el catálogo vacío.

## Verificación

```powershell
..\..\.venv\Scripts\python.exe manage.py test --settings=catalog_service.test_settings
```

La API y su esquema OpenAPI están disponibles en `/api/docs/` y `/api/schema/`.
