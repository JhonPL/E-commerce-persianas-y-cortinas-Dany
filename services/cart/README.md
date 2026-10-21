# Cart Service

Servicio Django dueño de los carritos de compra. El gateway conserva las rutas
que usa el frontend.

## Configuración y desarrollo

Configura `.env` con una base PostgreSQL independiente, `AUTH_SERVICE_URL`,
`CATALOGO_SERVICE_INTERNAL_URL` y el token interno compartido.

Desde la raíz del repositorio, el entorno Python compartido es `.venv`. Para
iniciar manualmente:

```powershell
..\..\.venv\Scripts\python.exe manage.py migrate
..\..\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8002
```

`.\run-local.ps1` inicia este servicio en el entorno local completo.

## Integraciones

- La identidad valida los tokens y es dueña de las cuentas de usuario.
- Los datos y precios vigentes de los productos se consultan en catálogo.
- Los IDs de usuario y producto se guardan como referencias entre servicios,
  sin claves foráneas a bases ajenas.
- El gateway coordina la verificación de referencias en pedidos y la limpieza
  del carrito antes de eliminar un producto.
- El pago simulado se procesa en `payments-simulator`; no se manejan cobros
  reales ni datos de tarjeta.

## Verificación

```powershell
..\..\.venv\Scripts\python.exe manage.py test --settings=cart_service.test_settings
```

La API y su esquema OpenAPI están disponibles en `/api/docs/` y `/api/schema/`.
