# Plan de despliegue demostrativo en la nube

**Proyecto:** Cortinas y Persianas — arquitectura de microservicios

**Revisado:** 29 de octubre de 2026

**Objetivo:** publicar una demostración educativa para una exposición de unos
15 minutos. No es producción comercial, no procesa pagos reales y no debe
conservarse funcionando después de la demostración.

> **Criterio principal:** que el flujo completo funcione durante la exposición:
> frontend, gateway, siete servicios, PostgreSQL, correo y vencimiento de
> pedidos. La opción gratuita se usará dentro de sus cuotas; ningún proveedor
> garantiza un costo total de cero si se exceden los límites.

## Decisión propuesta

| Parte | Servicio propuesto | Despliegue |
|---|---|---|
| Frontend React | Vercel Hobby | Sitio estático; `VITE_API_URL` apunta al gateway |
| Gateway | Render Free | Servicio Docker independiente; única API pública para el frontend |
| Identidad | Render Free | Servicio Docker independiente |
| Catálogo | Render Free | Servicio Docker independiente |
| Carrito | Render Free | Servicio Docker independiente |
| Pedidos | Render Free | Servicio Docker independiente |
| Notificaciones | Render Free | Servicio Docker independiente |
| Facturación | Render Free | Servicio Docker independiente; no forma parte del checkout actual |
| Simulador de pagos | Render Free | Servicio Docker independiente; solo resultados simulados |
| PostgreSQL | Neon Free | Un proyecto PostgreSQL para la demo, con una base lógica separada por servicio |
| Correo | Brevo Transactional Email API | HTTPS; Render Free bloquea SMTP saliente |
| Vencimiento de pedidos | cron-job.org Free | POST HTTPS cada minuto a un endpoint de pedidos con token dedicado |

Así se mantienen los ocho componentes de aplicación separados: el gateway y
los siete microservicios. El scheduler es una tarea operativa externa, no
reemplaza ni agrupa ninguno de esos componentes.

Vercel Hobby se plantea únicamente para una demo personal/educativa y no
comercial; se deben confirmar sus términos para la situación concreta. La
configuración de pagos debe seguir en modo demostrativo.

## Por qué esta combinación

- **Render Free** permite construir cada servicio desde el Dockerfile del
  repositorio y conservar los ocho procesos separados. Comparte 750 horas de
  instancia gratuitas por workspace y duerme un servicio tras 15 minutos sin
  tráfico; al despertar puede tardar alrededor de un minuto.
- **No se asociará una cuenta de facturación a Render.** Si se agota el ancho
  de banda gratuito sin método de pago, Render suspende los servicios. Si se
  agrega un método de pago, podrían aplicarse cargos por excedentes; no agregar
  uno para esta demo.
- **Neon Free** es permanente y no requiere tarjeta según su página actual.
  Su cómputo se suspende tras cinco minutos de inactividad, de modo que la
  primera consulta o migración puede tardar más. Las bases comparten los
  límites del proyecto.
- **Brevo** se invocará por su API HTTPS, no por SMTP. El remitente debe estar
  verificado en Brevo; `BREVO_API_KEY` se configurará solo como secreto de
  Render. El logo de los correos se servirá desde un endpoint público del
  servicio de notificaciones.
- **cron-job.org** admite ejecuciones de hasta una vez por minuto y cabeceras
  HTTP personalizadas. El endpoint de expiración tendrá un secreto propio,
  distinto de `INTERNAL_SERVICE_TOKEN`.
- **El frente de Vercel** debe configurarse con el URL público del gateway.
  Los despliegues Hobby se reservan para uso personal/no comercial.

### Costos y límites que deben revisarse

Las ocho aplicaciones Docker consumen las 750 horas compartidas del workspace
de Render, no 750 horas cada una. Aun así, una demo corta debe caber con margen
si no se dejan servicios activos después. Render también limita ancho de banda
y minutos de compilación; vigilar el panel de uso. Con un método de pago
asociado los excedentes pueden generar cargos; sin él, algunos límites
suspenden servicios o compilaciones. Neon Free comparte sus límites de cómputo,
almacenamiento y transferencia por proyecto.

## Alternativas evaluadas

### Google Cloud Run

Cloud Run admite el diseño de ocho servicios, pero exige asociar facturación
incluso si se intenta permanecer dentro de las cuotas gratuitas. El usuario
prefirió no habilitarla. Esta opción queda descartada salvo autorización
explícita posterior.

### Railway y Koyeb

Railway no encaja con ocho servicios separados en su Trial actual: permite
hasta cinco por proyecto y el crédito de prueba es temporal; el plan Free
ofrece USD 1 de crédito mensual. La página actual de Koyeb no anuncia un plan
gratuito de cómputo, así que no se incluye en el despliegue sin facturación.

## Cambios técnicos necesarios antes de desplegar

La preparación técnica local está lista, y la configuración de Neon ya se
rehizo y verificó. El repositorio incluye un Dockerfile reutilizable para
siete componentes, uno específico para facturación, un constructor de las
ocho imágenes, endpoints de salud y un script de activación. Render, Vercel,
Brevo y cron-job.org siguen pendientes.

### 1. Contenerizar los ocho componentes

- `deploy/Dockerfile` recibe el directorio y módulo WSGI como argumentos; se
  reutiliza para gateway y seis servicios.
- `deploy/Dockerfile.billing` añade dependencias nativas para facturación.
- `deploy/build-images.ps1` construye una imagen etiquetada por componente.
- Gunicorn está en los requisitos de los ocho componentes y las imágenes
  arrancan WSGI en `0.0.0.0:$PORT`. No usar Django `runserver` en la nube.
- En cada servicio Docker de Render, usar el contexto raíz del repositorio y
  `deploy/Dockerfile`; facturación usa `deploy/Dockerfile.billing`. Configurar
  los valores de build `SERVICE_PATH` y `WSGI_MODULE` para cada componente.
- Configurar la migración de cada base antes de aceptar tráfico. En la demo se
  puede usar un arranque idempotente `migrate --noinput` seguido de Gunicorn,
  con máximo una instancia por servicio; preferiblemente migrar una vez desde
  un paso controlado de despliegue.
- No guardar `.env`, contraseñas, tokens, archivos JSON protegidos ni claves
  SMTP/API en imágenes, variables `VITE_*`, logs o Git.
- Render proporciona `PORT`; URLs y secretos van en variables de entorno
  protegidas de cada servicio.

#### Alta manual de servicios en Render

Crear los servicios desde **New > Web Service**, conectando la rama
`V3-microservicios`. Para cada uno, dejar vacío **Root Directory**, usar
**Docker** como runtime, fijar el plan **Free** y configurar el Dockerfile y
los build arguments de esta tabla. El hostname definitivo se obtiene después
de crear cada servicio; usar ese hostname en las URLs de los servicios que lo
consumen.

| Servicio | Dockerfile | `SERVICE_PATH` | `WSGI_MODULE` |
|---|---|---|---|
| `cortinas-identity` | `deploy/Dockerfile` | `services/identity` | `auth_service.wsgi:application` |
| `cortinas-catalog` | `deploy/Dockerfile` | `services/catalog` | `catalog_service.wsgi:application` |
| `cortinas-cart` | `deploy/Dockerfile` | `services/cart` | `cart_service.wsgi:application` |
| `cortinas-notifications` | `deploy/Dockerfile` | `services/notifications` | `notification_service.wsgi:application` |
| `cortinas-billing` | `deploy/Dockerfile.billing` | `services/billing` | `billing_service.wsgi:application` |
| `cortinas-orders` | `deploy/Dockerfile` | `services/orders` | `orders_service.wsgi:application` |
| `cortinas-payments-simulator` | `deploy/Dockerfile` | `services/payments-simulator` | `payments_service.wsgi:application` |
| `cortinas-gateway` | `deploy/Dockerfile` | `gateway` | `gateway.wsgi:application` |

En cada servicio, configurar el health check como `/health/ready/`. En
**Environment**, agregar `DJANGO_DEBUG=False`, una `DJANGO_SECRET_KEY` única y
aleatoria, y `DJANGO_ALLOWED_HOSTS` con solo el hostname asignado, sin
`https://` ni ruta. En los siete servicios con base de datos agregar
`DATABASE_SSLMODE=require` y las cinco variables DB enumeradas en la sección
siguiente. No copiar `.env.example` completo: reemplazar URLs locales y
credenciales de ejemplo por valores reales de la demo.

Crear en este orden para conocer las URLs antes de configurar consumidores:
identidad, catálogo, notificaciones, carrito, facturación, pedidos, simulador
de pagos y, al final, gateway. Si el primer despliegue falla por variables
faltantes, añadirlas en el Dashboard y volver a desplegar; no publicar secretos
en el repositorio para automatizar esta parte.

### 2. Bases y datos de muestra

- El proyecto Neon de la demo ya existe en AWS US West 2 (Oregon), rama
  `production`. Sus siete bases están separadas por servicio y pertenecen a
  roles de aplicación creados por SQL:

  | Base | Rol propietario |
  |---|---|
  | `identity_service` | `identity_app` |
  | `catalogo` | `catalog_app` |
  | `cart_service` | `cart_app` |
  | `orders_service` | `orders_app` |
  | `notifications_service` | `notifications_app` |
  | `billing_service` | `billing_app` |
  | `cortinas_payments_simulator` | `payments_app` |

- Los roles ya tienen contraseñas nuevas generadas por Neon. Sus archivos
  individuales `.env` están en `%USERPROFILE%\Downloads` y fuera del
  repositorio; no subirlos ni copiar sus valores al chat.
- Las migraciones Django ya se aplicaron a las siete bases desde las imágenes
  Docker locales de cada microservicio, usando conexión directa a Neon y TLS.
  Aún no se han cargado usuarios, productos ni pedidos de demostración.
- Configurar en cada servicio sus variables actuales `*_DB_NAME`, `*_DB_USER`,
  `*_DB_PASSWORD`, `*_DB_HOST` y `*_DB_PORT`; los settings actuales no están
  basados en una variable única `DATABASE_URL`.
- Usar el hostname y usuario proporcionados por Neon; `*_DB_PORT` es `5432`.
  La variable de contraseña contiene la contraseña del rol de Neon y cada
  `*_DB_NAME` debe ser el nombre de la base aislada para ese servicio.
- Habilitar TLS requerido por Neon (`sslmode=require`) en la conexión Django.
  Usar credenciales distintas por base cuando sea posible y guardar las URLs
  privadas en las variables protegidas de Render.
- Aplicar migraciones y cargar solo datos ficticios mínimos: categorías,
  productos, usuario de prueba y rol admin. No copiar datos reales del
  monolito ni datos de clientes.
- Limitar instancias y conexiones para respetar los límites del plan gratuito;
  usar el endpoint pooled de Neon si el volumen de conexiones lo requiere.

### 3. Variables y comunicación entre servicios

- Configurar en Gateway las URLs HTTPS de Render para identidad, catálogo, carrito,
  pedidos, notificaciones y simulador de pagos.
- Configurar en pedidos las URLs de carrito, catálogo y notificaciones;
  configurar en carrito la URL de identidad/catálogo; configurar en el
  simulador la URL de pedidos. Revisar todas las variables `*_SERVICE_URL` en
  settings y `.env.example` de cada servicio.
- Sustituir los valores de ejemplo por los hostnames HTTPS asignados por
  Render, conservando exactamente las rutas:
  - **Gateway:** `IDENTITY_SERVICE_URL=https://<identity-host>`;
    `CATALOGO_SERVICE_URL=https://<catalog-host>/api/v1/catalogo`;
    `CATALOGO_SERVICE_INTERNAL_URL=https://<catalog-host>/api/internal/catalogo`;
    `CART_SERVICE_URL=https://<cart-host>/api/v1/carrito`;
    `CART_SERVICE_INTERNAL_URL=https://<cart-host>/api/internal/carrito`;
    `ORDERS_SERVICE_URL=https://<orders-host>`;
    `PAYMENTS_SERVICE_URL=https://<payments-host>/api/v1/payments`;
    `NOTIFICATIONS_SERVICE_URL=https://<notifications-host>`.
  - **Catálogo y carrito:** `AUTH_SERVICE_URL=https://<identity-host>/api/v1/auth/me/`.
    En carrito, `CATALOGO_SERVICE_INTERNAL_URL=https://<catalog-host>/api/internal/catalogo`.
  - **Pedidos:** `AUTH_SERVICE_URL=https://<identity-host>/api/v1/auth/me/`;
    `CATALOGO_SERVICE_INTERNAL_URL=https://<catalog-host>/api/internal/catalogo`;
    `CART_SERVICE_URL=https://<cart-host>`;
    `NOTIFICATIONS_SERVICE_URL=https://<notifications-host>`;
    `BILLING_SERVICE_URL=https://<billing-host>`.
  - **Simulador:** `AUTH_SERVICE_URL=https://<identity-host>/api/v1/auth/me/`;
    `ORDERS_SERVICE_URL=https://<orders-host>`.
  En Gateway, `CORS_ALLOWED_ORIGINS` debe ser el origen exacto de Vercel
  (incluye `https://`, sin ruta final). En notificaciones, usar ese mismo
  origen en `FRONTEND_URL` y la URL propia asignada en
  `NOTIFICATIONS_PUBLIC_URL`.
- Todas las llamadas entre servicios usarán HTTPS. Los endpoints internos
  conservarán `X-Internal-Service-Token`; emitir un token aleatorio fuerte y
  cargarlo como secreto en cada componente que lo necesite.
- Configurar `PAYMENT_SIMULATOR_ENABLED=True` únicamente en el servicio
  `cortinas-payments-simulator`; no habilita ni integra pagos reales.
- En Render Free los servicios web se comunican por URLs públicas, no por una
  red privada entre servicios. Mantener la validación JWT/token interno y no
  incluir secretos en Vite. Publicar solo el gateway como URL de API del
  frontend.
- En el gateway: `DEBUG=False`, `ALLOWED_HOSTS` con el hostname asignado,
  `CORS_ALLOWED_ORIGINS` con el origen exacto de Vercel y timeouts compatibles
  con los arranques en frío. No usar comodines de CORS con credenciales.
- En frontend: definir `VITE_API_URL` antes de compilar el sitio y verificar
  que no se publique ninguna llave privada.
- Configurar en el proveedor OAuth de Google los orígenes y callback/redirect
  URI de la URL pública final; probar registro/login OAuth en el dominio de
  demostración.

### 4. Correo y destinatarios

- Configurar `EMAIL_BACKEND=notificaciones.brevo_email_backend.BrevoEmailBackend`
  y un remitente verificado en Brevo. SMTP está bloqueado en Render Free.
- Guardar `BREVO_API_KEY` como secreto, nunca en
  `.env.example`, imagen Docker o frontend.
- Configurar `NOTIFICATIONS_PUBLIC_URL` con la URL HTTPS pública de
  notificaciones; Brevo usará esa URL para mostrar el logo de los correos.
- Probar, en este orden: formulario de contacto al administrador; confirmación
  del pedido al cliente; notificación al administrador solo tras aprobación
  simulada; rechazo/vencimiento al cliente; cambios de estado al cliente y
  descarga del PDF adjunto.
- Verificar que `NotificacionAdmin` registra el resultado/idempotencia y que
  los errores de API se reflejan en logs sin incluir claves ni contenido
  sensible.

### 5. Salud y activación desde cero

- Los ocho backends exponen `GET /health/live/` y `GET /health/ready/`. Las
  respuestas son mínimas y no revelan secretos/configuración.
- `live` verifica que el proceso responde. `ready` verifica la base de datos en
  los siete servicios y devuelve `503` cuando no está disponible; el gateway
  no tiene dependencia de base de datos propia.
- Configurar el health check de cada servicio Render como `/health/ready/`.
- `scripts/warm-demo.ps1` valida por HTTPS los nueve destinos (frontend,
  gateway y siete servicios). El script:
  1. Solicitar `/health/ready/` a cada backend, en paralelo o por lotes.
  2. Reintentar respuestas de arranque/en frío con espera incremental y tiempo
     máximo por servicio.
  3. Consultar Neon de forma indirecta mediante `ready`, evitando exponer
     credenciales.
  4. Esperar a que el gateway, login y rutas de negocio estén listos; fallar
     claramente si algún componente no despierta.
  5. Mostrar URL y estado por servicio, sin imprimir tokens.
- Ejecutar el script justo antes de la exposición. El endpoint de activación
  despierta servicios que estaban dormidos; Render puede volver a dormirlos
  tras 15 minutos sin tráfico.

### 6. Vencimiento automático de pedidos

El comando actual `expire_unpaid_orders --loop` es un proceso infinito pensado
para el lanzador local. No debe arrancarse como un proceso infinito dentro del
servidor HTTP de Render.

- El servicio de pedidos expone
  `POST /api/internal/pedidos/expire-unpaid-orders/`, protegido por el
  encabezado `X-Expiration-Job-Token`.
- Configurar `EXPIRATION_JOB_TOKEN` como un secreto aleatorio dedicado; no
  reutilizar `INTERNAL_SERVICE_TOKEN`.
- Configurar cron-job.org con método POST, frecuencia `* * * * *`, URL HTTPS del
  servicio de pedidos y el token en el encabezado. La ejecución puede retrasar
  hasta un minuto la transición posterior al vencimiento de cinco minutos.
- Validar que la ruta rechaza solicitudes sin token y que una ejecución
  autenticada rechaza pedidos vencidos y envía la notificación.
- Pausar o eliminar el cron-job.org tras la exposición.

## Guion de preparación y exposición

### Configuración manual segura de los servicios

Crear los servicios desde el repositorio `JhonPL/E-commerce-persianas-y-cortinas-Dany`,
rama `V3-microservicios`, región Oregon, plan Free y contexto de build raíz. En
cada servicio Docker usar `/health/ready/` como health check y cargar las
variables desde el panel de Render. No enviar contraseñas, tokens ni claves API
por el chat ni incluirlas en el repositorio.

| Servicio Render | Dockerfile | `SERVICE_PATH` | `WSGI_MODULE` |
|---|---|---|---|
| `cortinas-identity` (ya desplegado) | `deploy/Dockerfile` | `services/identity` | `auth_service.wsgi:application` |
| `cortinas-catalog` | `deploy/Dockerfile` | `services/catalog` | `catalog_service.wsgi:application` |
| `cortinas-cart` | `deploy/Dockerfile` | `services/cart` | `cart_service.wsgi:application` |
| `cortinas-orders` | `deploy/Dockerfile` | `services/orders` | `orders_service.wsgi:application` |
| `cortinas-notifications` | `deploy/Dockerfile` | `services/notifications` | `notification_service.wsgi:application` |
| `cortinas-billing` | `deploy/Dockerfile.billing` | `services/billing` | `billing_service.wsgi:application` |
| `cortinas-payments-simulator` | `deploy/Dockerfile` | `services/payments-simulator` | `payments_service.wsgi:application` |
| `cortinas-gateway` | `deploy/Dockerfile` | `gateway` | `gateway.wsgi:application` |

Para cada servicio con base, mapear el archivo de credenciales local de su rol
(`*_app.env`) en el panel de Render: `PGDATABASE` a `<PREFIJO>_DB_NAME`,
`PGUSER` a `<PREFIJO>_DB_USER`, `PGPASSWORD` a `<PREFIJO>_DB_PASSWORD`,
`PGHOST` a `<PREFIJO>_DB_HOST` y `PGPORT` a `<PREFIJO>_DB_PORT`. Los prefijos
son `IDENTITY`, `CATALOGO`, `CART`, `ORDERS`, `NOTIFICATIONS`, `BILLING` y
`PAYMENTS`, respectivamente. Añadir también `DATABASE_SSLMODE=require`,
`DJANGO_DEBUG=False`, un `DJANGO_SECRET_KEY` único por servicio y
`DJANGO_ALLOWED_HOSTS` con el hostname exacto asignado por Render.

Generar un valor aleatorio fuerte para `INTERNAL_SERVICE_TOKEN` y cargar el
mismo valor en los servicios que se comunican internamente y en el gateway.
Generar otro valor independiente para `EXPIRATION_JOB_TOKEN`; solo se configura
en pedidos y en el scheduler. Nunca reutilizar la clave Django como token.

Variables adicionales por servicio:

- **Catálogo:** `AUTH_SERVICE_URL`, `SERVICE_TIMEOUT_SECONDS`,
  `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY` y `CLOUDINARY_API_SECRET`.
- **Carrito:** `AUTH_SERVICE_URL`, `CATALOGO_SERVICE_INTERNAL_URL` y
  `SERVICE_TIMEOUT_SECONDS`.
- **Pedidos:** `AUTH_SERVICE_URL`, `CATALOGO_SERVICE_INTERNAL_URL`,
  `CART_SERVICE_URL`, `NOTIFICATIONS_SERVICE_URL`, `BILLING_SERVICE_URL` y
  `SERVICE_TIMEOUT_SECONDS`.
- **Notificaciones:** `EMAIL_BACKEND=notificaciones.brevo_email_backend.BrevoEmailBackend`,
  `BREVO_API_KEY`, `ADMIN_EMAIL`, `CONTACT_EMAIL`, `DEFAULT_FROM_EMAIL`,
  `FRONTEND_URL` y `NOTIFICATIONS_PUBLIC_URL`. El remitente debe estar
  verificado en Brevo; SMTP no funciona desde Render Free.
- **Facturación:** `INTERNAL_SERVICE_TOKEN`. No participa en el checkout
  normal, pero se despliega como componente independiente.
- **Simulador de pagos:** `AUTH_SERVICE_URL`, `ORDERS_SERVICE_URL`,
  `PAYMENT_SIMULATOR_ENABLED=True` y `SERVICE_TIMEOUT_SECONDS`. Es solo una
  simulación: no recopila tarjetas ni procesa dinero.
- **Gateway:** `IDENTITY_SERVICE_URL`, `CATALOGO_SERVICE_URL`,
  `CATALOGO_SERVICE_INTERNAL_URL`, `CART_SERVICE_URL`,
  `CART_SERVICE_INTERNAL_URL`, `ORDERS_SERVICE_URL`, `PAYMENTS_SERVICE_URL`,
  `NOTIFICATIONS_SERVICE_URL`, `CORS_ALLOWED_ORIGINS` y los timeouts del
  `.env.example`. `CORS_ALLOWED_ORIGINS` debe ser el origen HTTPS exacto de
  Vercel, sin comodines.
- **Identidad:** ya está desplegado. Si se usa login de Google, configurar
  `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` y los URI autorizados tanto en
  Render como en Google Cloud Console.

Las URLs previstas siguen el nombre del servicio, por ejemplo
`https://cortinas-catalog.onrender.com`; después de crear cada recurso, copiar
la URL que muestra Render y actualizar las referencias entre servicios con
esa URL real. Para las rutas, conservar exactamente las del `.env.example`:
`AUTH_SERVICE_URL` termina en `/api/v1/auth/me/`;
`CATALOGO_SERVICE_URL` termina en `/api/v1/catalogo`;
`CATALOGO_SERVICE_INTERNAL_URL` termina en `/api/internal/catalogo`;
`CART_SERVICE_URL` es la URL base del servicio cuando la consume pedidos y
termina en `/api/v1/carrito` cuando la consume el gateway;
`CART_SERVICE_INTERNAL_URL` termina en `/api/internal/carrito`;
`PAYMENTS_SERVICE_URL` termina en `/api/v1/payments`.

Publicar `frontend` en Vercel con `npm run build`, directorio de salida `dist`
y `VITE_API_URL=https://<gateway-host-real>/api/v1`. Confirmar esa variable
antes de compilar; el `.env.production` del repositorio aún apunta a una URL
antigua y no debe usarse como destino de la demo. Después de publicar Vercel,
volver al gateway y a notificaciones para fijar el origen final de Vercel en
`CORS_ALLOWED_ORIGINS` y `FRONTEND_URL`. El frontend no debe recibir tokens,
contraseñas ni claves privadas.

No considerar terminado el despliegue hasta que estén configurados directamente
en sus paneles las credenciales de Neon, Brevo, Cloudinary y Google OAuth que
se vayan a usar; cada URL HTTPS responda `GET /health/ready/` con HTTP 200; y
se complete el recorrido de aceptación de esta sección. El envío real de
correo, el acceso OAuth y las imágenes dependen de sus claves externas
correspondientes.

### Un día antes (o la mañana de la exposición)

1. Conectar el repositorio a Render y Vercel; comprobar los límites gratuitos
   del workspace de Render y no agregar un método de pago.
2. Confirmar que los archivos de credenciales Neon están guardados fuera del
   repositorio y ejecutar las migraciones de las siete bases vacías.
3. Crear ocho servicios Docker independientes en Render. Para cada uno, elegir
   el Dockerfile/contexto del repositorio y configurar `SERVICE_PATH`,
   `WSGI_MODULE`, variables de DB, URLs y secretos.
4. Publicar frontend en Vercel con el URL definitivo del gateway.
5. Configurar dominios, HTTPS, CORS y redirects OAuth.
6. Configurar Brevo, verificar el remitente y guardar la API key en Render.
7. Configurar cron-job.org con el token exclusivo de expiración.
8. Ejecutar recorrido completo: login, catálogo, carrito, checkout, aprobación
   simulada, correo al cliente/admin, rechazo, expiración a cinco minutos y
   cambio de estado por el administrador.

### Diez minutos antes

1. Ejecutar `warm-demo.ps1`; comprobar que todos los health checks responden.
2. Abrir la URL de Vercel en una ventana privada y probar el flujo una vez con
   datos ficticios y buzones de demostración.
3. Revisar logs de cada servicio y confirmar que no hay errores de base, CORS,
   OAuth, tokens o API de correo.
4. Mantener a mano URLs directas de salud/documentación de servicios para
   mostrar su despliegue, pero hacer el recorrido de usuario por el gateway.
5. Si un servicio está dormido, volver a ejecutar el activador y esperar la
   confirmación `ready`; no cambiar variables ni redeplegar durante la charla.

### Después de la exposición

1. Deshabilitar el job de cron-job.org.
2. Suspender o eliminar los ocho servicios Render; el scale-to-zero no elimina
   el proyecto ni los datos.
3. Borrar las bases Neon si ya no se necesitan; el plan Free escala a cero,
   pero conserva los datos y el proyecto.
4. Despublicar/pausar el frontend si no debe quedar visible y revocar las
   claves temporales de Brevo/scheduler que ya no se usarán.

## Criterios de aceptación

- [ ] Frontend HTTPS accesible y usando únicamente el gateway como API base.
- [ ] Ocho componentes desplegados por separado; cada backend tiene salud y
  URL verificables.
- [ ] Cada servicio persiste en su propia base lógica; ninguna migración crea
  claves foráneas entre bases de servicios distintos.
- [ ] OAuth/login, catálogo, carrito, pedidos, administración y contacto
  funcionan desde la URL pública.
- [ ] El simulador aprueba/rechaza sin solicitar ni guardar datos de tarjetas.
- [ ] El administrador solo recibe el detalle del pedido después de la
  aprobación simulada; cliente recibe confirmaciones/cambios correspondientes.
- [ ] Brevo API probado desde Render con remitente verificado, mensajes,
  adjuntos PDF y notificaciones a los destinatarios correctos.
- [ ] El pedido pendiente se rechaza al pasar cinco minutos y se notifica al
  cliente aun si no llega otra petición de usuario.
- [ ] El endpoint de expiración requiere su token dedicado y el scheduler se
  ejecuta cada minuto.
- [ ] El script de activación despierta instancias dormidas, espera readiness y
  reporta claramente fallos.
- [ ] No hay secretos en el repositorio, imágenes, navegador o logs.
- [ ] Pago y facturación están claramente identificados como demostrativos/no
  conectados al checkout real.
- [ ] Tras la exposición, se pausa el scheduler y los servicios que no deban
  quedar activos se eliminan o suspenden.

## Estado

La preparación local está validada: las ocho imágenes se reconstruyeron en
Docker Desktop después de los cambios de Brevo y expiración programada; todas
pasaron `manage.py check` y la comprobación de configuración de Gunicorn.
También pasaron las suites locales de los ocho componentes y la validación
sintáctica de los scripts PowerShell. El commit `3594f2e` ya está publicado en
la rama `V3-microservicios`.

El proyecto Neon inicial fue eliminado y se recreó como `cortinas-persianas-demo`
(Project ID `withered-truth-84643412`), en AWS US West 2 (Oregon), rama
`production` (Branch ID `br-rapid-frog-aruqmuys`). Se verificó el acceso al SQL
Editor como `neondb_owner`; también se comprobó que los siete roles de aplicación
pueden crearse mediante SQL y que Neon permite generarles una contraseña nueva
desde **Reset password** cuando ya tienen una contraseña temporal.

Los siete roles se crearon por SQL con `LOGIN` y `NOINHERIT`. La consulta de
verificación confirmó para todos: sin `SUPERUSER`, `CREATEDB` ni `CREATEROLE`,
y sin membresías de otros roles. Las siete bases de la tabla anterior fueron
creadas después y se verificó que cada una pertenece al rol correspondiente.
Las contraseñas nuevas se descargaron como archivos `.env` por rol en
`%USERPROFILE%\Downloads`; ningún valor de contraseña se añadió al repositorio
ni al chat. Mantener esos archivos fuera de Git y usarlos al configurar Render.

Las siete conexiones autenticadas se probaron desde un contenedor Docker con
el driver PostgreSQL: cada una devolvió su usuario y base correctos con
`sslmode=require`. Las migraciones Django de identidad, catálogo, carrito,
pedidos, notificaciones, facturación y simulador terminaron correctamente;
pedidos incluye la migración de estados de checkout predefinidos. No se
ejecutaron seeds de usuarios, productos ni pedidos. Neon Free puede suspender
el compute por inactividad; ese comportamiento es normal.

Render está en el plan Hobby, sin tarjeta registrada. Se creó el primer servicio
de esta demo: `cortinas-identity`, en Oregon, desde la rama
`V3-microservicios` y con el Dockerfile `deploy/Dockerfile`. Render informó
`Deploy succeeded`; Gunicorn inició y el log confirmó que la instancia quedó
disponible. El endpoint `https://cortinas-identity.onrender.com/health/ready/`
respondió HTTP 200 con JSON. El archivo temporal usado para cargar variables a
Render se eliminó después de la configuración.

Los otros seis servicios y el gateway aún no se han creado. Tampoco se ha
publicado el frontend en Vercel, configurado Brevo o activado el scheduler. No
se ha probado el envío real de correo ni la expiración programada desde la
nube. Se añadió arriba una matriz de Dockerfiles, rutas WSGI, variables y URLs
previstas para completar manualmente la configuración de los paneles sin
compartir secretos por el chat. La identidad está desplegada, pero el flujo
público completo sigue pendiente.

## Referencias oficiales consultadas

- [Render Free limitations](https://render.com/docs/free)
- [Render Docker deploys](https://render.com/docs/docker)
- [Render Blueprint specification](https://render.com/docs/blueprint-spec)
- [Neon pricing](https://neon.com/pricing)
- [cron-job.org](https://cron-job.org/en/)
- [Vercel Hobby plan](https://vercel.com/docs/plans/hobby)
- [Vercel Terms of Service](https://vercel.com/legal/terms)
- [Render private networking](https://render.com/docs/private-network)
- [Railway pricing](https://railway.com/pricing)
- [Railway Free Trial limits](https://docs.railway.com/pricing/free-trial)
- [Koyeb pricing](https://www.koyeb.com/pricing)
- [Brevo transactional email API](https://developers.brevo.com/docs/send-a-transactional-email)
