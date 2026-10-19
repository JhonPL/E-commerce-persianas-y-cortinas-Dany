# Gateway

Gateway stateless de entrada para el frontend. Reenvía las rutas públicas a los
servicios dueños de sus datos y compone el dashboard administrativo desde las
métricas internas de identidad, catálogo y pedidos. No tiene aplicaciones de
negocio ni base de datos propia.

## Desarrollo local

El frontend debe apuntar a `http://127.0.0.1:8010/api/v1`. El gateway usa el
puerto 8010 por defecto; el puerto 8000 queda reservado para el backend legacy
mientras se conserva como rollback.

```powershell
.\run-local.ps1
```

El script usa el entorno Python de `backend\venv` y la configuración protegida
en `%LOCALAPPDATA%\CortinasPersianas\config\backend.json`; no guarda secretos en
el repositorio. Inicia un servicio con
`services\run-local.ps1 -Service catalog` (cambia `catalog` por el nombre del
servicio) o mediante las tareas de VS Code. El token interno debe coincidir con
el de los servicios que atienden llamadas internas.

## Rutas

- Identidad, catálogo, carrito, pedidos y simulador: proxies transparentes que
  mantienen los contratos `/api/v1/...` existentes.
- Dashboard: verifica el rol mediante identidad y combina métricas de servicios
  internos.
- Borrado de producto: valida el rol de administrador, comprueba referencias en
  pedidos, limpia el carrito y luego solicita el borrado al catálogo.
- `/health/`: comprobación de vida sin dependencias de base de datos.

## Verificación

```powershell
..\backend\venv\Scripts\python.exe manage.py test gateway --settings=gateway.test_settings
```