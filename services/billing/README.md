# Billing Service

Microservicio Django dueño de los registros de facturación. Mantiene referencias
a pedidos mediante `pedido_id`, sin claves foráneas entre servicios.

El servicio expone una API interna de persistencia, protegida por
`X-Internal-Service-Token`, y usa una base PostgreSQL independiente. La
facturación aún no genera, firma ni transmite documentos a la DIAN y no forma
parte del checkout simulado.

## Configuración y desarrollo

Configura `.env` con las credenciales de la base y el token interno compartido.
Desde la raíz, el entorno Python es `.venv`:

```powershell
..\..\.venv\Scripts\python.exe manage.py migrate
..\..\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8006
```

Endpoints:

- `GET /api/internal/facturas/`: lista facturas.
- `POST /api/internal/facturas/`: guarda una factura ya preparada.
- `GET /api/internal/facturas/pedido/{pedido_id}/`: consulta la factura
  asociada.
- `PATCH /api/internal/facturas/pedido/{pedido_id}/`: actualiza campos de
  persistencia.

## Verificación

```powershell
..\..\.venv\Scripts\python.exe manage.py test --settings=billing_service.test_settings
```

La documentación OpenAPI está disponible en `/api/docs/` y `/api/schema/`.
