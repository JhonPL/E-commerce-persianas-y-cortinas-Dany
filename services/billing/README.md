# Billing Service

Microservicio Django con PostgreSQL propio para persistir los registros
existentes de `Factura`. La extracción conserva los campos de factura y
reemplaza la relación local con `Pedido` por `pedido_id`: no existe una FK
cruzada entre las bases de pedidos y facturación.

El sistema legacy solo contenía el modelo; no tenía rutas HTTP, pantallas,
generación de XML/PDF ni comunicación real con DIAN. Este corte mueve el modelo
y los datos existentes y agrega una API interna de persistencia. **No genera,
firma ni transmite facturas.** El código de pagos permanece sin cambios.

## Configuración

Copia `.env.example` a `.env`, configura la base PostgreSQL independiente y
usa el mismo `INTERNAL_SERVICE_TOKEN` compartido por los servicios:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 127.0.0.1:8006
```

Todos los endpoints de facturación requieren `X-Internal-Service-Token`:

- `GET /api/internal/facturas/`: lista facturas.
- `POST /api/internal/facturas/`: guarda una factura ya preparada.
- `GET /api/internal/facturas/pedido/{pedido_id}/`: consulta la factura asociada.
- `PATCH /api/internal/facturas/pedido/{pedido_id}/`: actualiza campos de
  persistencia.

El servicio no está conectado a una ruta del frontend o a pagos porque no había
un contrato HTTP de facturación implementado que conservar.

## Transferencia de datos

Con una copia de seguridad verificable del backend, exporta desde `backend` a
una ubicación protegida fuera del proyecto:

```powershell
python manage.py export_invoices --file C:\secure-transfer\invoices.json
```

Luego importa en la base vacía del servicio:

```powershell
python manage.py import_invoices C:\secure-transfer\invoices.json
```

La transferencia conserva IDs, referencias a pedido, número de factura, CUFE,
URLs de XML/PDF, estado, bandera DIAN y fechas. El archivo contiene datos
comerciales y URLs de documentos; no lo imprimas ni subas al repositorio. En
Windows, utiliza una carpeta cifrada o con ACL restringidas y elimina el
archivo después de validar los conteos. La importación rechaza bases que ya
tengan facturas.

No se han transferido datos reales ni conectado bases PostgreSQL durante este
corte.

## Verificación

```powershell
python manage.py test --settings=billing_service.test_settings
```

La documentación OpenAPI está disponible en `/api/docs/` y `/api/schema/`.
