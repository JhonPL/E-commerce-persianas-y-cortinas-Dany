# Cart Service

Servicio Django independiente para carritos de compra. El backend conserva las
rutas `/api/v1/carrito/` como proxy, de modo que el frontend mantiene su
contrato actual.

## Datos y entorno

El servicio usa una base PostgreSQL propia. Copia `.env.example` a `.env`,
configura los valores y configura `INTERNAL_SERVICE_TOKEN` con el mismo valor en
`backend/.env`, `catalog-service/.env`, `cart-service/.env` y
`orders-service/.env` y `auth-service/.env`.

Instala dependencias y aplica migraciones desde esta carpeta:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 127.0.0.1:8002
```

## Migración de datos

Antes de cambiar el tráfico, exporta los ítems existentes desde la raíz
`Cortinas-Pers` y carga el fixture en esta carpeta:

```powershell
python backend\manage.py dumpdata carrito.CarritoItem --indent 2 --output carrito.json
python cart-service\manage.py loaddata carrito.json
```

La estructura del fixture conserva los IDs de usuario, producto e ítem; en este
servicio `usuario` es un identificador entero, no una relación con la base de
identidad. No subas el fixture al repositorio: puede contener datos privados.
Realiza y verifica una copia de seguridad de la base antes de la exportación y
de la migración.

El identificador de secuencia para `item_id` queda actualizado por la carga de
fixtures de Django. Tras verificar el conteo y contenido importado, inicia el
servicio en el puerto 8002 y el backend en el puerto 8000. El backend reenvía
las rutas existentes del carrito a este servicio.

## Integraciones

- La autenticación de usuario se valida contra
  `AUTH_SERVICE_URL` (`auth-service/api/v1/auth/me/`); `auth-service` es dueño
  de la identidad y de los JWT.
- La información y disponibilidad de productos se consulta al endpoint interno
  de `catalog-service`, protegido por `INTERNAL_SERVICE_TOKEN`.
- El borrado de un producto solicita al backend que compruebe referencias en
  pedidos. Si no hay pedidos, el backend solicita a este servicio limpiar sus
  ítems antes de permitir el borrado.
- El endpoint interno `DELETE /api/internal/carrito/productos/{id}/` solo
  acepta el token entre servicios.
- Pagos y pedidos permanecen en el backend durante esta etapa.

## Verificación

```powershell
python manage.py test --settings=cart_service.test_settings
```

La API y el esquema OpenAPI están disponibles en `/api/docs/` y `/api/schema/`.
