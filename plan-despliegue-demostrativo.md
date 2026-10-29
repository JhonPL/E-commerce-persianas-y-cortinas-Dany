# Plan de despliegue demostrativo en la nube

**Proyecto:** Cortinas y Persianas — arquitectura de microservicios

**Revisado:** 28 de octubre de 2026

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

## Cambios técnicos necesarios antes de crear recursos

El despliegue cloud sigue pendiente, pero ya comenzó la preparación técnica
local. El repositorio incluye un Dockerfile reutilizable para siete
componentes, uno específico para facturación, un constructor de las ocho
imágenes, endpoints de salud y un script de activación. No se ha configurado
un proyecto cloud ni se han creado recursos.

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

- Crear un proyecto Neon para la demo y una base distinta para cada dueño de
  datos: identidad, catálogo, carrito, pedidos, notificaciones, simulador de
  pagos y facturación.
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

### Un día antes (o la mañana de la exposición)

1. Conectar el repositorio a Render y Vercel; comprobar los límites gratuitos
   del workspace de Render y no agregar un método de pago.
2. Crear las bases en Neon, cargar secretos y ejecutar migraciones.
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

Este documento sigue siendo un plan, no un despliegue cloud ejecutado. La
preparación local ya tiene los Dockerfiles, los ocho endpoints de salud y los
scripts de construcción/activación. Las ocho imágenes se reconstruyeron en
Docker Desktop después de los cambios de Brevo y expiración programada; todas
pasaron `manage.py check` y la comprobación de configuración de Gunicorn.
También pasaron las suites locales de los ocho componentes y la validación
sintáctica de los scripts PowerShell.

Todavía no se han creado servicios en Render, bases en Neon ni secretos, y no
se ha probado el envío real de Brevo ni el vencimiento programado desde Render.
El proyecto tiene un repositorio Git, pero no se ha conectado a las cuentas de
Render, Vercel, Neon o Brevo. Falta configurar las cuentas, cargar sus secretos
en los paneles y validar el flujo público completo. No se ha compartido ni
guardado ninguna credencial.

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
