# Identity Service

Servicio Django dueño de autenticación, usuarios, roles y perfiles de cliente.
El gateway mantiene el contrato HTTP que consume el frontend; los demás
servicios validan las sesiones mediante las APIs internas de identidad.

## Configuración y desarrollo

Configura `.env` con su base PostgreSQL independiente, una `DJANGO_SECRET_KEY`
aleatoria y el `INTERNAL_SERVICE_TOKEN` compartido por los servicios. Google
OAuth usa el cliente y los redirect URIs configurados para la aplicación.

Desde la raíz del repositorio, el entorno Python compartido es `.venv`. Para
iniciar manualmente:

```powershell
..\..\.venv\Scripts\python.exe manage.py migrate
..\..\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8004
```

En el flujo local habitual, `.\run-local.ps1` inicia este servicio junto con el
gateway, los demás microservicios y el frontend.

## Datos e integraciones

- PostgreSQL de este servicio es la fuente de verdad para roles, usuarios y
  perfiles.
- Los IDs de usuario son identificadores opacos que carrito, pedidos y pagos
  simulados guardan sin claves foráneas entre bases.
- Las APIs de autenticación, administración y métricas se publican a través del
  gateway o de endpoints internos autenticados.
- El servicio no procesa pagos. `payments-simulator` se integra usando el ID
  del usuario y las APIs internas de pedidos.

## Verificación

```powershell
..\..\.venv\Scripts\python.exe manage.py test --settings=auth_service.test_settings
```

La documentación OpenAPI está disponible en `/api/docs/` y `/api/schema/`.
