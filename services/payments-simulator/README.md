# Simulador de pagos

Este servicio es únicamente demostrativo: no se conecta a una pasarela real, no
autoriza cargos y no solicita ni almacena números de tarjeta o códigos de
seguridad en el backend. El checkout acepta únicamente números ficticios y los
usa en el navegador para escoger el resultado; los campos de tarjeta no se
incluyen en la petición. Usa `4242 4242 4242 4242` para aprobación y
`4000 0000 0000 0002` para rechazo, con cualquier vencimiento futuro y CVC
ficticio de tres dígitos.

Después de una aprobación, el servicio de pedidos solicita a billing un PDF de
demostración y lo envía como adjunto en el correo de confirmación. Ese PDF no
es una factura electrónica validada por la DIAN ni prueba un cobro real.

## Ejecución local

Para crear la base y el rol PostgreSQL dedicados, guardar secretos fuera del
repositorio y aplicar las migraciones, ejecuta desde la raíz:

```powershell
.\services\payments-simulator\provision-local.ps1
```

El script solicita la clave administrativa de PostgreSQL como entrada segura;
no la guarda ni la imprime. Los secretos del servicio se guardan en
`%LOCALAPPDATA%\CortinasPersianas\config\payments.json`. Luego inicia el servicio
desde otra terminal:

```powershell
.\services\payments-simulator\run-local.ps1
```

El simulador queda deshabilitado por defecto si no se configura
`PAYMENT_SIMULATOR_ENABLED`; el script local lo habilita únicamente para el
entorno de desarrollo. No habilites pagos simulados en producción.

La API autenticada es `POST /api/v1/payments/simulate/`, con `pedido_id`,
`outcome` (`approved` o `declined`) y un `request_id` UUID que funciona como
clave de idempotencia. El servicio obtiene el total y propietario del pedido
desde el servicio de pedidos; no confía en importes suministrados por el
cliente.