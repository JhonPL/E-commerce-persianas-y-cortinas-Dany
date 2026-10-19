# Catalog Service

Servicio Django independiente para productos, categorías e imágenes. Conserva el
contrato HTTP existente en `/api/v1/catalogo/`; el backend actual actúa como
proxy para que el frontend y los clientes existentes no tengan que cambiar sus
URLs durante esta etapa.

## Datos y entorno

El servicio requiere su propia base PostgreSQL. Copia `.env.example` a `.env`,
configura sus variables y usa un `INTERNAL_SERVICE_TOKEN` largo y aleatorio,
idéntico al configurado en `backend/.env`, `cart-service/.env` y
`orders-service/.env` y `auth-service/.env`. No reutilices la base del monolito.

Instala dependencias y aplica las migraciones desde esta carpeta:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 127.0.0.1:8001
```

## Migración inicial del catálogo

Con el backend todavía conectado a la base de datos actual, exporta los datos
antes de dirigir las rutas hacia este servicio:

```powershell
python backend\manage.py dumpdata catalogo --indent 2 --output catalogo.json
python catalog-service\manage.py loaddata catalogo.json
```

El fixture no se debe subir al repositorio si contiene datos de clientes u otra
información privada. El catálogo exportado contiene los IDs actuales, categorías,
productos e imágenes (incluidas sus URLs de Cloudinary).

Después de cargar el fixture, configura el mismo `INTERNAL_SERVICE_TOKEN` en los
dos archivos de entorno y aplica las migraciones del monolito. Estas eliminan
las claves foráneas de su base hacia las tablas del catálogo, conservando los
IDs de producto:

```powershell
python backend\manage.py migrate
```

Después inicia este servicio en el puerto 8001 y el backend actual en el puerto
8000. El backend reenvía las rutas existentes `/api/v1/catalogo/` al servicio.
Los modelos y migraciones `catalogo` del monolito se conservan temporalmente
para el historial de migraciones; sus rutas y su administración ya no escriben
en las tablas antiguas.

Para entornos de demostración sin fixture, ejecuta primero
`python manage.py seed_demo_catalog` en este servicio. Después se puede ejecutar
`python manage.py seed_demo` en el backend para generar usuarios y pedidos que
referencian los IDs del catálogo remoto.

## Integración durante esta etapa

- El backend mantiene las rutas actuales y las reenvía al servicio.
- Carrito y pedidos consultan el endpoint interno de productos para no mantener
  claves foráneas hacia la base de datos del catálogo.
- La identidad y los JWT son responsabilidad de `auth-service`; las operaciones
  administrativas validan el JWT contra su endpoint `/api/v1/auth/me/`.
- Antes de borrar un producto, el servicio solicita al backend actual que
  compruebe referencias en pedidos y solicite a `cart-service` eliminar los
  ítems que lo referencian, manteniendo la regla anterior de no borrar
  productos presentes en pedidos.
- La aplicación `pagos` no forma parte de este corte.

## Verificación

```powershell
python manage.py test --settings=catalog_service.test_settings
```

La API y su esquema OpenAPI quedan disponibles en `/api/docs/` y `/api/schema/`.
