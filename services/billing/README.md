# Billing Service

Microservicio Django dueño de los registros y comprobantes de facturación.
Mantiene referencias a pedidos mediante `pedido_id`, sin claves foráneas entre
servicios.

El servicio expone una API interna protegida por `X-Internal-Service-Token` y
usa una base PostgreSQL independiente. `POST /api/internal/facturas/demo-pdf/`
registra idempotentemente el pedido y genera un PDF A4 con el logo local,
categorías e iconos locales de persianas, cortinas y accesorios, medidas,
precios e información de pago. Utiliza ReportLab, ya incluido en este servicio,
sin depender de imágenes externas ni incorporar otra dependencia de renderizado.
Los SVG originales y sus PNG de uso en ReportLab están en
`facturacion/assets/icons/`; incluyen las licencias MIT de IconMind y Tabler.
El PDF lleva un identificador y un QR etiquetados como demostración no fiscal.
Su tipografía de contenido mantiene una talla uniforme de 7,5 pt; el color, la
negrita y los fondos distinguen las secciones. No se firma ni se transmite a la
DIAN y no tiene validez fiscal.

## Configuración y desarrollo

Configura `.env` con las credenciales de la base y el token interno compartido.
`INVOICE_ISSUER_ADDRESS`, `INVOICE_ISSUER_PHONE` e `INVOICE_ISSUER_EMAIL` son
opcionales y permiten agregar datos de contacto del emisor. Si no se configuran,
el PDF identifica esos datos como demostración académica.
Desde la raíz, el entorno Python es `.venv`:

```powershell
..\..\.venv\Scripts\python.exe manage.py migrate
..\..\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8006
```

Endpoints:

- `POST /api/internal/facturas/demo-pdf/`: genera el PDF de demostración para
  un pedido aprobado. La API de pedidos expone la descarga autenticada en
  `/api/v1/pedidos/{pedido_id}/factura/` y verifica propietario/rol antes de
  solicitar el documento.
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
