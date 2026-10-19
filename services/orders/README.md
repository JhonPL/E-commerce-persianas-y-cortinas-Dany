# Orders Service

Servicio Django independiente para pedidos, sus detalles, estados, historial y
direcciones de entrega. El backend conserva las rutas públicas y de
administración como proxy; el frontend mantiene sus URLs actuales.

## Datos y entorno

El servicio usa una base PostgreSQL propia. Copia `.env.example` a `.env`,
configura los valores y establece `INTERNAL_SERVICE_TOKEN` con el mismo valor
en el backend y en los servicios que realicen llamadas internas; debe coincidir
entre cada servicio que se comunica.

Instala dependencias y aplica migraciones desde esta carpeta:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 127.0.0.1:8003
```

## Transferencia de datos

Primero crea un respaldo verificado de la base monolítica. Ejecuta la
exportación desde `backend` mientras el backend todavía usa la base actual:

```powershell
python manage.py export_orders --output ..\orders-service\orders-export.json
```

La exportación incluye pedidos, líneas, estados, historial, las direcciones
asociadas y una copia de nombre/correo para presentar pedidos históricos. No
exporta contraseñas ni credenciales de usuario. El archivo contiene
información personal y debe mantenerse fuera del repositorio y protegerse
durante la transferencia.

Con `orders-service` conectado a su base vacía y con las migraciones aplicadas:

```powershell
python manage.py import_orders --input orders-export.json
```

La importación conserva los IDs de pedidos, detalles, direcciones, ciudades,
departamentos y estados, y rechaza una base que ya contenga datos. Compara los
conteos de origen e importación antes de redirigir tráfico. No ejecutes el
corte sobre la base real hasta tener una copia de seguridad recuperable.

Si necesitas datos de demostración, ejecuta el sembrado del monolito **antes**
de exportar e importar. El comando heredado `seed_demo` aún crea pedidos en la
base del monolito y no debe ejecutarse después de redirigir el tráfico.

## Integraciones y alcance

- `auth-service` es dueño de identidad y JWT; las solicitudes de usuario se
  validan contra su endpoint configurado en `AUTH_SERVICE_URL`.
- Los detalles de producto se consultan a `catalog-service`.
- El checkout obtiene los artículos de `cart-service` y calcula el total en
  este servicio; no confía en importes enviados por el navegador.
- `payments-simulator` consulta el pedido por una API interna autenticada y
  reporta el resultado simulado. No procesa cobros ni recibe datos de tarjetas.
- Un rechazo queda registrado para que el cliente pueda reintentar sobre el
  mismo pedido, pero no aparece en la cola de trabajo del administrador ni
  puede contarse como venta.
- Después de la aprobación, el estado inicial de preparación lo asigna el
  sistema. El administrador solo puede avanzar el pedido en orden: de
  “Pendiente de preparación” a “Preparado” y después a “Enviado”.
- El backend comprueba con este servicio si un producto está asociado a pedidos
  antes de permitir borrarlo y después limpia el carrito mediante
  `cart-service`.
- Los registros y tablas heredados de pedidos permanecen en la base del
  monolito durante esta etapa para conservar el grafo de migraciones y las
  relaciones legacy. Las APIs públicas activas leen y escriben en este
  servicio.
- Facturación y notificaciones son servicios separados; sus referencias a
  pedidos son identificadores, no relaciones de base de datos entre servicios.

## Verificación

```powershell
python manage.py test --settings=orders_service.test_settings
```

La API y el esquema OpenAPI están disponibles en `/api/docs/` y `/api/schema/`.
