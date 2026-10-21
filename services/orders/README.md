# Orders Service

Servicio Django dueño de pedidos, detalles, estados, historial y direcciones de
entrega. Usa su propia base PostgreSQL; los IDs de usuario y producto son
referencias a los servicios de identidad y catálogo, no claves foráneas entre
bases.

## Configuración y desarrollo

Configura `.env` con las credenciales de la base, las URL de identidad, catálogo,
carrito y notificaciones, y el token interno compartido.

Desde la raíz, el entorno Python es `.venv`. Para iniciar manualmente:

```powershell
..\..\.venv\Scripts\python.exe manage.py migrate
..\..\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8003
```

El arranque local completo usa `.\run-local.ps1`: aplica las migraciones e
inicia los siete servicios, el gateway, el frontend y el monitor de pagos
vencidos.

## Integraciones y comportamiento

- El checkout obtiene el carrito y calcula el total en este servicio; no confía
  en importes enviados por el navegador.
- Guarda el nombre del producto como copia histórica junto a su identificador.
- `payments-simulator` consulta el pedido mediante una API interna autenticada y
  comunica el resultado; no procesa cobros reales ni tarjetas.
- Si un pedido no recibe aprobación dentro de cinco minutos, pasa a “Pago
  rechazado”, se registra el cambio y se notifica al cliente. Un pago tardío se
  rechaza.
- El aviso inicial confirma la recepción únicamente al cliente. El administrador
  recibe los detalles del pedido solo tras la aprobación simulada.
- Tras aprobarse el pago, el PDF académico se genera desde los datos guardados,
  se adjunta a ambos correos y se puede descargar desde `Mis pedidos`. La ruta
  de descarga comprueba en Django que el pedido pertenece al cliente autenticado
  (o que quien consulta es administrador); los pedidos pendientes/rechazados no
  permiten descargarlo.
- Los pedidos sin pago no aparecen en la cola de administración ni se cuentan
  como ventas.
- Los estados posteriores a la aprobación avanzan de “Pendiente de preparación”
  a “Preparado” y luego “Enviado”. Cada cambio notifica al cliente.

El comando `expire_unpaid_orders` permite comprobar vencimientos una sola vez o
mantener un monitor activo:

```powershell
..\..\.venv\Scripts\python.exe manage.py expire_unpaid_orders
..\..\.venv\Scripts\python.exe manage.py expire_unpaid_orders --loop --interval 10
```

## Verificación

```powershell
..\..\.venv\Scripts\python.exe manage.py test --settings=orders_service.test_settings
```

La API y su esquema OpenAPI están disponibles en `/api/docs/` y `/api/schema/`.
