# Billing Service

Microservicio Django dueño de los registros y comprobantes de facturación.
Mantiene referencias a pedidos mediante `pedido_id`, sin claves foráneas entre
servicios.

El servicio expone una API interna protegida por `X-Internal-Service-Token` y
usa una base PostgreSQL independiente. `POST /api/internal/facturas/demo-pdf/`
registra idempotentemente el pedido, prepara el contexto con los datos recibidos
y renderiza `facturacion/templates/facturacion/invoice.html` con
`facturacion/assets/invoice.css`. La plantilla adapta la maqueta HTML de
referencia a A4 sin cambiar su composición: utiliza localmente el logo extraído
de esa referencia (`logogreen-reference.png`), Montserrat y la fuente de firma,
además de los tres PNG aportados para las categorías de persianas, cortinas y
accesorios. Los iconos SVG de identidad y contacto se conservan en la plantilla.
El QR se crea localmente como SVG. El CUFE de demostración y el QR se etiquetan
como no fiscales; el documento no se firma ni se transmite a la DIAN y no tiene
validez fiscal.

La presentación y los iconos SVG de la maqueta se editan en la plantilla HTML;
las dimensiones, tipografía y estilos de impresión se ajustan en el CSS. Las
fuentes, el logo y las ilustraciones de producto deben permanecer como recursos
locales en `facturacion/assets/`. La preparación de valores, el formato
monetario, la selección de icono por categoría, la paginación de descripciones
largas y los datos del QR se encuentran en `facturacion/invoice_data.py`.
`facturacion/pdf.py` solo renderiza la plantilla y la convierte a PDF. El
fetcher de WeasyPrint limita imágenes y estilos a los assets locales y a la
imagen de datos del QR. En pedidos de una sola página, el pie se alinea cerca
de la franja inferior; en facturas con continuación permanece en el flujo del
contenido para evitar solaparse con las tarjetas.

## Configuración y desarrollo

Configura `.env` con las credenciales de la base y el token interno compartido.
La dirección, teléfono, correo y NIT del emisor tienen los valores indicados
por el negocio como valores predeterminados. Se pueden reemplazar con
`INVOICE_ISSUER_ADDRESS`, `INVOICE_ISSUER_PHONE`, `INVOICE_ISSUER_EMAIL` e
`INVOICE_ISSUER_NIT`; `INVOICE_ISSUER_WEBSITE` es opcional.

WeasyPrint requiere bibliotecas nativas además de los paquetes Python. En
Windows, instala el GTK 3 Runtime y agrega su carpeta `bin` al `PATH` antes de
iniciar Django (por ejemplo,
`$env:PATH = "C:\Program Files\GTK3-Runtime Win64\bin;$env:PATH"`). En
Debian/Ubuntu instala las bibliotecas de Pango, HarfBuzz, GDK-PixBuf y fontconfig descritas en la
[guía oficial de instalación de WeasyPrint](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation).
La versión `WeasyPrint==70.0` y `qrcode==8.2` están fijadas en
`requirements.txt`; ReportLab fue retirado porque no tenía otros usos en el
repositorio.

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

En Windows, las pruebas que invocan WeasyPrint se omiten explícitamente si no
están instaladas sus bibliotecas GTK/Pango; las pruebas restantes comprueban
validaciones, preparación de datos y selección local de iconos.

La documentación OpenAPI está disponible en `/api/docs/` y `/api/schema/`.
