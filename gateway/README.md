# Gateway

Gateway stateless de entrada para el frontend. Enruta las APIs públicas a los
servicios dueños de sus datos y compone el dashboard administrativo. No tiene
base de datos de negocio.

## Desarrollo local

El frontend usa `http://127.0.0.1:8010/api/v1`. Desde la raíz del repositorio,
ejecuta `.\run-local.ps1` para iniciar frontend, gateway, los siete
microservicios y el monitor de vencimiento de pagos pendientes.

El proyecto comparte el entorno Python `.venv` de la raíz, requiere
`frontend\node_modules`, las configuraciones protegidas en
`%LOCALAPPDATA%\CortinasPersianas\config` y las bases locales disponibles. Las
variables del gateway se guardan en `gateway.json`; no guardes secretos en el
repositorio.

Para iniciar solo el gateway desde esta carpeta, ejecuta:

```powershell
.\run-local.ps1
```

Inicia un microservicio con `services\run-local.ps1 -Service catalog`; sustituye
`catalog` por `identity`, `cart`, `orders`, `notifications`, `billing` o
`payments-simulator`. Las dependencias Python compartidas están definidas en
los archivos `requirements.txt` de cada servicio.

## Rutas y comportamiento

- Identidad, catálogo, carrito, pedidos y simulador: proxies que conservan los
  contratos HTTP consumidos por el frontend.
- El proxy del carrito espera hasta 90 segundos para dar margen al arranque en
  frío de la instancia gratuita de Render.
- El checkout tiene un timeout dedicado de 30 segundos para completar sus
  llamadas a pedidos y notificaciones.
- `POST /api/v1/contacto/` reenvía el formulario al servicio de notificaciones;
  el token interno nunca se expone al navegador.
- El dashboard combina métricas internas de identidad, catálogo y pedidos.
- El borrado de productos verifica referencias en pedidos y limpia el carrito
  antes de pedir al catálogo que elimine el producto.
- `/health/` comprueba que el gateway está activo sin depender de bases de
  datos.

## Verificación

```powershell
..\.venv\Scripts\python.exe manage.py test gateway --settings=gateway.test_settings
```
