# Cortinas y Persianas — Microservicios

Esta rama contiene la aplicación local basada en microservicios. Cada servicio
de negocio está separado por responsabilidad; `gateway` es el único punto de
entrada del frontend.

## Componentes

| Componente | Puerto | Responsabilidad |
|---|---:|---|
| Gateway | 8010 | API de entrada, enrutamiento y dashboard |
| Catálogo | 8001 | Productos, categorías e imágenes |
| Carrito | 8002 | Carritos y sus artículos |
| Pedidos | 8003 | Checkout, pedidos, direcciones y estados |
| Identidad | 8004 | Usuarios, sesiones y roles |
| Notificaciones | 8005 | Correos de pedidos y contacto |
| Facturación | 8006 | Persistencia de facturas |
| Simulador de pagos | 8007 | Aprobación/rechazo simulado; no procesa cobros reales |
| Frontend | 5173 | Aplicación React |

Cada servicio es dueño de su base de datos. Las relaciones entre servicios son
identificadores y llamadas HTTP internas; no hay claves foráneas entre sus
bases.

Consulta el [diagrama de arquitectura](./architecture-microservices.html) para
ver los servicios, los flujos principales y los límites de datos.
El archivo [microservicios-plantuml.txt](./microservicios-plantuml.txt) contiene
código PlantUML para diagramas de secuencia, casos de uso, clases, componentes
y despliegue.

## Requisitos locales

- Python 3.13.
- Node.js y npm.
- PostgreSQL con las bases de los servicios ya provisionadas.
- Configuraciones protegidas en
  `%LOCALAPPDATA%\CortinasPersianas\config`: `gateway.json`, `identity.json`,
  `catalog.json`, `cart.json`, `orders.json`, `notifications.json`, `billing.json`
  y `payments.json`.
- `frontend\.env` configurado con
  `VITE_API_URL=http://127.0.0.1:8010/api/v1`.

Prepara una sola vez el entorno Python compartido desde la raíz:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install `
  -r gateway\requirements.txt `
  -r services\identity\requirements.txt `
  -r services\catalog\requirements.txt `
  -r services\cart\requirements.txt `
  -r services\orders\requirements.txt `
  -r services\notifications\requirements.txt `
  -r services\billing\requirements.txt `
  -r services\payments-simulator\requirements.txt
npm ci --prefix frontend
```

Inicia todos los servicios, el monitor que rechaza pedidos sin pagar a los
cinco minutos, el gateway y el frontend:

```powershell
.\run-local.ps1
```

automáticamente al arrancar.
Abre `http://localhost:5173`. Mantén abiertas las ventanas de terminales que
inició el script. Las migraciones de pedidos y facturación se aplican
automáticamente al arrancar.

## Pruebas

Cada microservicio tiene sus ajustes de pruebas con SQLite aislado:

```powershell
.\.venv\Scripts\python.exe services\identity\manage.py test --settings=auth_service.test_settings
.\.venv\Scripts\python.exe services\catalog\manage.py test --settings=catalog_service.test_settings
.\.venv\Scripts\python.exe services\cart\manage.py test --settings=cart_service.test_settings
.\.venv\Scripts\python.exe services\orders\manage.py test --settings=orders_service.test_settings
.\.venv\Scripts\python.exe services\notifications\manage.py test --settings=notification_service.test_settings
.\.venv\Scripts\python.exe services\billing\manage.py test --settings=billing_service.test_settings
.\.venv\Scripts\python.exe services\payments-simulator\manage.py test --settings=payments_service.test_settings
.\.venv\Scripts\python.exe gateway\manage.py test gateway --settings=gateway.test_settings
```

Para pruebas de navegador, prepara las bases de datos locales e inicia el
entorno completo antes de ejecutar `frontend\run-e2e-local.ps1`.

## Configuración sensible

Las contraseñas, tokens y secretos se mantienen fuera del repositorio, en la
configuración protegida local o en el gestor de secretos correspondiente. No
subas archivos `.env`, configuraciones protegidas, respaldos ni datos de
clientes.
