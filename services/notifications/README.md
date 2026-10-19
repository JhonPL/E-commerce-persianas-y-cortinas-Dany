# Notification Service

Servicio Django independiente para notificaciones administrativas y su historial
de entrega. Recibe el evento de pedido aprobado desde el puente de pagos en el
backend monolítico; el módulo de pagos no se cambia en esta etapa.

## Configuración

El servicio requiere su propia base PostgreSQL. Copia `.env.example` a `.env`,
configura la base y establece `INTERNAL_SERVICE_TOKEN` con el mismo valor que
en `backend/.env`.

Por defecto, el backend de correo imprime mensajes en la consola para
desarrollo. Para enviar correo, configura `EMAIL_BACKEND` como
`django.core.mail.backends.smtp.EmailBackend` y proporciona `EMAIL_HOST`,
`EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS` y
`DEFAULT_FROM_EMAIL` desde variables de entorno. No guardes credenciales en el
repositorio. `ADMIN_EMAIL` recibe los avisos.

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

- El endpoint `POST /api/internal/notificaciones/pedidos/` requiere
  `X-Internal-Service-Token`. No está expuesto como ruta pública del frontend.
- El puente legacy envía el ID de pedido, correo del cliente y total. El
  servicio envía el mismo aviso que enviaba la función anterior y registra el
  resultado en su propia base.
- La clave `pedido:{id}:payment-approved` evita volver a enviar un aviso
  confirmado cuando el webhook repite la solicitud. Solicitudes duplicadas
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
