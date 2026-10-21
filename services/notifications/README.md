# Notification Service

Servicio Django dueño de notificaciones de pedidos y del formulario de
contacto, con plantillas de correo y registro de entregas.

## Configuración y desarrollo

Configura `.env` con una base PostgreSQL independiente, el token interno
compartido y credenciales SMTP. La cuenta remitente SMTP
`jhon.paternina302@gmail.com` solo envía; no es destinataria. `ADMIN_EMAIL`
recibe los avisos administrativos y `CONTACT_EMAIL` aparece en el pie del
correo. El cliente recibe notificaciones en la dirección asociada a su pedido.

En Gmail se necesita una contraseña de aplicación. Guárdala solo en
`%LOCALAPPDATA%\CortinasPersianas\config\notifications.json` o en el gestor de
secretos del entorno; nunca en el repositorio.

Desde la raíz, el entorno Python compartido es `.venv`. Para iniciar
manualmente:

```powershell
..\..\.venv\Scripts\python.exe manage.py migrate
..\..\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8005
```

## Flujos de notificación

- El formulario de contacto envía los datos al buzón administrativo y permite
  responder al correo del cliente.
- Crear un pedido pendiente no envía correos.
- Cuando el simulador aprueba el pago, el administrador recibe un único correo
  «Nuevo pedido recibido» con los datos completos del pedido, y el cliente
  recibe su correo de pago confirmado.
- Los cambios de estado y vencimientos de pago se notifican al cliente. Estos
  avisos se mantienen independientes del correo de pago confirmado.
- Los eventos se identifican de forma idempotente por destinatario para evitar
  correos duplicados y registrar reintentos o errores SMTP.
- Las referencias a pedidos son IDs; no hay claves foráneas entre las bases de
  notificaciones y pedidos.

## Verificación

```powershell
..\..\.venv\Scripts\python.exe manage.py test --settings=notification_service.test_settings
```

La API y su esquema OpenAPI están disponibles en `/api/docs/` y `/api/schema/`.
