# Notification Service

Servicio Django independiente para notificaciones de pedidos y contacto, con
plantillas HTML de marca y registro de entrega.

## Configuración

El servicio requiere su propia base PostgreSQL. Copia `.env.example` a `.env`,
configura la base y establece `INTERNAL_SERVICE_TOKEN` con el mismo valor que
en el gateway y los servicios que lo llaman.

`jhon.paternina302@gmail.com` es exclusivamente la cuenta remitente y de
autenticación SMTP; no se usa como destinatario de los mensajes del sistema.
`ADMIN_EMAIL` es el buzón receptor de avisos administrativos y `CONTACT_EMAIL`
es la dirección que aparece en el pie de los correos (ambos usan el correo
administrativo si no se configuran por separado). `FRONTEND_URL` determina el
destino de los botones de seguimiento; usa la URL pública en producción. El
cliente recibe sus mensajes en el correo asociado a su pedido o al formulario
de contacto. Para Gmail,
`EMAIL_HOST_PASSWORD` debe ser una contraseña de aplicación generada para la
cuenta remitente. Guarda ese secreto únicamente en la configuración local
protegida o en el gestor de secretos de producción; nunca en el repositorio.
La plantilla `.env.example` incluye los parámetros SMTP, pero su contraseña
es solo un marcador de posición.

La configuración usa Gmail por SMTP (TLS en el puerto 587). Configura una
contraseña de aplicación válida para la cuenta en `EMAIL_HOST_PASSWORD` usando
la configuración local protegida o el gestor de secretos de producción. No
guardes credenciales en el repositorio.

En desarrollo local, el archivo protegido es
`%LOCALAPPDATA%\CortinasPersianas\config\notifications.json`. Reinicia
`services\run-local.ps1 -Service notifications` después de cambiarlo para que
el servicio cargue los nuevos valores. En producción, establece las mismas
variables en el gestor de secretos del entorno desplegado.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 127.0.0.1:8005
```

## Transferencia de historial

Haz primero una copia de seguridad verificable de la base del backend. Exporta
el historial a una ubicación protegida y fuera del repositorio:

```powershell
cd backend
python manage.py export_notification_history --file C:\secure-transfer\notifications.json
```

Importa en la base vacía del servicio:

```powershell
cd notification-service
python manage.py import_notification_history C:\secure-transfer\notifications.json
```

Se preservan IDs de notificación, ID numérico de pedido, destinatario,
resultado, fecha, número de intentos y detalle de error. El pedido es un ID,
no una FK remota. El archivo contiene correos y datos operativos: no lo
imprimas, compartas ni subas al repositorio; en Windows, usa una carpeta
cifrada o con ACL de acceso restringido y elimínalo después de validar los
conteos.

No se exportó ni importó historial real en este corte.

## Flujo y límites

- Los endpoints internos requieren `X-Internal-Service-Token`; el token nunca
  se envía al navegador.
- `POST /api/internal/notificaciones/contacto/` envía al buzón administrativo los
  datos del formulario y configura el correo del cliente como respuesta.
- La creación de un pedido pendiente no envía correos. Cuando el pago se
  aprueba, `POST /api/internal/notificaciones/pedidos/` envía un único correo
  al administrador con el asunto «Nuevo pedido recibido» y todos los detalles
  de entrega y productos.
- `POST /api/internal/notificaciones/pedidos/estado/` notifica al cliente cada
  cambio de estado realizado por el administrador. Cada transición se identifica
  con su registro de historial para evitar correos duplicados.
- Los correos de pedido comparten una plantilla adaptable a móvil con el logo
  integrado en el mensaje, resumen de productos, total, dirección disponible y
  enlaces a la gestión de pedidos o a la cuenta del cliente. Los estados del
  servicio se muestran como pedido confirmado, en preparación y en camino.
  Transportadora, guía y entrega final no se muestran porque la aplicación aún
  no registra esos datos/estados.
- `POST /api/internal/notificaciones/pedidos/` informa únicamente al
  administrador que el pago fue confirmado, con el resumen y los nombres de los
  productos. El diseño aclara que el simulador no realiza cobros reales.
- Cuando el servicio de pedidos rechaza un pago vencido después de cinco
  minutos, utiliza la notificación de cambio de estado para informar al cliente.
- Los correos de pedidos se registran por destinatario y evento para evitar
  reenvíos cuando se repite una solicitud confirmada.
- La clave `pedido:{id}:payment-approved` deduplica el correo administrativo
  cuando se repite la confirmación del pago.
  Solicitudes duplicadas
  durante un envío activo no envían otro correo; si un proceso deja un intento
  activo por más de 30 segundos, la siguiente solicitud puede recuperarlo. Un
  intento fallido puede reintentarse y queda reflejado en el contador y estado.
- Si el servicio no responde, el puente conserva un registro de fallo en la
  tabla legacy de notificaciones y registra el error; así el webhook de pagos
  conserva su comportamiento actual. Esta compatibilidad temporal puede dejar
  esos registros de contingencia junto al historial migrado.
- Pagos continúa en el monolito y no se cambió. El servicio no procesa pagos;
  solo recibe el aviso que genera el webhook existente.

## Verificación

```powershell
python manage.py test --settings=notification_service.test_settings
```

La documentación OpenAPI está disponible en `/api/docs/` y `/api/schema/`.
