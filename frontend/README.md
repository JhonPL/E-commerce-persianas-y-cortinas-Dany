# Persianas y Cortinas Dany — Frontend

**Proyecto:** E-Commerce Persianas y Cortinas Dany  
**Universidad:** Universidad Cooperativa de Colombia, Sede Villavicencio  
**Stack:** React 19 · Vite 7 · CSS Modules · React Router v7

---

## 1. Requisitos

| Herramienta | Versión mínima |
|-------------|----------------|
| Node.js     | 18.x           |
| Yarn        | 1.22.x         |

---

## 2. Instalación

```bash
# Instalar dependencias
yarn install

# Iniciar servidor de desarrollo
yarn dev

# Compilar para producción
yarn build
```

### Dependencias principales

```bash
yarn add react-router-dom lucide-react recharts react-is
```

> **Importante:** `recharts` requiere `react-is` como peer dependency. Sin él lanza un error en tiempo de ejecución.

---

## 3. Variables de entorno

Crea un archivo `.env` en la raíz del proyecto frontend:

```env
VITE_CLOUDINARY_CLOUD_NAME=tu_cloud_name
VITE_CLOUDINARY_UPLOAD_PRESET=cortinas_dany
```

**Configuración de Cloudinary:**
1. Crea una cuenta en [cloudinary.com](https://cloudinary.com)
2. Ve a **Settings → Upload → Upload presets → Add preset**
3. Modo: **Unsigned**
4. Folder sugerida: `cortinas-dany/productos`

---

## 4. Estructura del proyecto

```
src/
├── App.jsx                          ← Router principal, providers y guards
├── styles/
│   └── globals.css                  ← Variables CSS, reset, fuentes globales
├── context/
│   ├── AuthContext.jsx              ← Estado global de autenticación
│   └── CartContext.jsx              ← Estado global del carrito
├── components/
│   ├── Navbar/
│   │   ├── Navbar.jsx               ← Barra de navegación auth-aware
│   │   └── Navbar.module.css
│   ├── Hero/
│   │   ├── Hero.jsx                 ← Banner principal de la tienda
│   │   └── Hero.module.css
│   ├── ProductCard/
│   │   ├── ProductCard.jsx          ← Tarjeta de producto en catálogo
│   │   └── ProductCard.module.css
│   ├── CartDrawer/
│   │   ├── CartDrawer.jsx           ← Panel lateral del carrito
│   │   └── CartDrawer.module.css
│   ├── WhatsAppButton/
│   │   ├── WhatsAppButton.jsx       ← Botón flotante WhatsApp
│   │   └── WhatsAppButton.module.css
│   └── Footer/
│       ├── Footer.jsx
│       └── Footer.module.css
└── pages/
    ├── Home/
    │   ├── Home.jsx                 ← Página de inicio
    │   └── Home.module.css
    ├── Tienda/
    │   ├── Tienda.jsx               ← Catálogo con filtros
    │   └── Tienda.module.css
    ├── Detalle/
    │   ├── Detalle.jsx              ← Detalle de producto + calculadora m²
    │   └── Detalle.module.css
    ├── Contacto/
    │   ├── Contacto.jsx             ← Formulario de contacto + mapa
    │   └── Contacto.module.css
    ├── MisPedidos/
    │   ├── MisPedidos.jsx           ← Historial de pedidos (RequireAuth)
    │   └── MisPedidos.module.css
    ├── NotFound/
    │   ├── NotFound.jsx             ← Página 404
    │   └── NotFound.module.css
    ├── Auth/
    │   ├── Auth.jsx                 ← Layout split login/registro
    │   ├── LoginForm.jsx
    │   ├── RegisterForm.jsx
    │   └── Auth.module.css
    └── Admin/
        ├── AdminLayout.jsx          ← Sidebar + topbar del panel admin
        ├── Admin.module.css
        ├── AdminDashboard.jsx       ← Métricas, gráficas, alertas
        ├── Dashboard.module.css
        ├── AdminProductos.jsx       ← CRUD productos + gestión de fotos
        ├── AdminProductos.module.css
        ├── AdminPedidos.jsx         ← Gestión y cambio de estado de pedidos
        ├── AdminPedidos.module.css
        ├── AdminUsuarios.jsx        ← Gestión de usuarios
        └── AdminUsuarios.module.css
```

---

## 5. Rutas

| Ruta | Componente | Acceso |
|------|-----------|--------|
| `/` | `Home` | Público |
| `/tienda` | `Tienda` | Público |
| `/producto/:id` | `Detalle` | Público |
| `/contacto` | `Contacto` | Público |
| `/login` | `Auth` | Público (sin Navbar/Footer) |
| `/mis-pedidos` | `MisPedidos` | `RequireAuth` |
| `/checkout` | `Checkout` | `RequireAuth` |
| `/admin` | `AdminDashboard` | `RequireAdmin` |
| `/admin/productos` | `AdminProductos` | `RequireAdmin` |
| `/admin/pedidos` | `AdminPedidos` | `RequireAdmin` |
| `/admin/usuarios` | `AdminUsuarios` | `RequireAdmin` |
| `*` | `NotFound` | Público |

### Guards de ruta

**`RequireAuth`** — si el usuario no tiene sesión, redirige a `/login` guardando `state.from` para volver al destino original después del login.

**`RequireAdmin`** — si no hay sesión redirige a `/login`; si hay sesión pero el rol no es `admin`, redirige a `/`.

---

## 6. Contextos globales

### AuthContext

Maneja el estado de autenticación en toda la aplicación.

**Estado:**
```js
{
  user:    { usuario_id, nombre, email, rol },  // null si no hay sesión
  token:   string | null,
  loading: boolean,
  error:   string | null
}
```

**Funciones expuestas:**
```js
const { user, token, loading, error, login, register, logout, clearError } = useAuth()
```

| Función | Descripción |
|---------|-------------|
| `login(email, password)` | Autentica al usuario. Retorna `{ success, rol }` o `{ success: false, error }` |
| `register(nombre, email, password)` | Registra un nuevo cliente. Retorna `{ success }` o `{ success: false, error }` |
| `logout()` | Limpia el estado. En `AdminLayout` usa `window.location.href = '/'` para limpiar el historial del navegador |
| `clearError()` | Limpia el mensaje de error |

La autenticación se realiza contra el servicio de identidad a través del gateway local.

---

### CartContext

Maneja el carrito de compras globalmente. El carrito es accesible sin sesión y se conserva al hacer login.

**Estado:**
```js
{
  items:  [{ producto_id, nombre, ancho, alto, area, precioM2, precioTotal, cantidad }],
  total:  number,
  count:  number,
  isOpen: boolean
}
```

**Funciones expuestas:**
```js
const { items, total, count, isOpen, addItem, removeItem, updateMedidas, toggleCart, closeCart, clearCart } = useCart()
```

**Lógica de negocio:**
- La key de cada ítem es `${producto_id}-${ancho}-${alto}` — mismo producto con medidas distintas genera ítems separados.
- `area = (ancho × alto) / 10.000` (resultado en m²)
- `precioTotal = area × precio_m2`

---

## 7. Componentes

### Navbar
Auth-aware. Con sesión activa muestra avatar con dropdown (nombre, enlace a Mis Pedidos, cerrar sesión). Sin sesión muestra botón "Ingresar".

### CartDrawer
Panel lateral deslizable desde la derecha. Muestra los ítems del carrito con sus medidas y precios. Incluye botón para proceder al checkout.

### WhatsAppButton
Botón flotante en la esquina inferior derecha presente en todas las páginas públicas. Enlace directo: `https://wa.me/573001234567`.

### ProductCard
Tarjeta de producto usada en el catálogo. Muestra imagen principal, nombre, categoría, precio por m² y botón para ver detalle.

### Hero
Banner principal de la página de inicio con imagen de fondo, título y llamada a la acción.

---

## 8. Páginas — Tienda pública

### Home (`/`)
Página de bienvenida con Hero, sección de categorías destacadas y productos recientes.

### Tienda (`/tienda`)
Catálogo completo con filtros por categoría y barra de búsqueda. Muestra `ProductCard` por cada producto activo.

### Detalle (`/producto/:id`)
Vista completa del producto con galería de imágenes, descripción y calculadora de precio:
- El cliente ingresa **ancho** y **alto** en cm
- Se calcula el área en m² y el precio total automáticamente
- Botón "Agregar al carrito" que guarda las medidas junto al producto

### Contacto (`/contacto`)
- Tarjetas con dirección, teléfono, correo y horario de atención
- Formulario enviado a `POST /api/v1/contacto/`; el gateway lo reenvía al
  servicio de notificaciones y el administrador lo recibe por SMTP
- Botón de WhatsApp directo
- Mapa embed de Google Maps (Villavicencio)
- Formulario con validación, estado de éxito y errores de envío visibles

En producción, `jhon.paternina302@gmail.com` será la cuenta SMTP del sistema
y el destinatario administrativo de los mensajes de contacto y pedidos. Esa
cuenta también enviará las notificaciones de cambio de estado a los clientes;
su configuración y credenciales SMTP se realizarán más adelante.

### MisPedidos (`/mis-pedidos`) — RequireAuth
Historial de pedidos del cliente autenticado:
- Cards colapsables por pedido con barra de progreso de 3 estados
- Tabla de ítems con medidas y precios
- Estado vacío con enlace a la tienda

### Checkout (`/checkout`) — RequireAuth
- El servicio de pedidos calcula y persiste el pedido usando el carrito y catálogo.
- El simulador permite aprobar o rechazar la transacción sin datos de tarjeta ni cobros reales.
- Al rechazar, el historial muestra el pedido como rechazado y el carrito se conserva.
- Al aprobar, se vacía el carrito y el pedido queda disponible para su gestión administrativa.

### NotFound (`*`)
Página 404 con animación y botones de navegación (inicio, tienda, volver atrás).

---

## 9. Páginas — Autenticación

### Auth (`/login`)
Layout split: formulario a la izquierda, panel decorativo a la derecha.

**LoginForm:**
- Botón OAuth Google (UI lista, flujo pendiente)
- Campo email + contraseña con toggle de visibilidad
- Checkbox "Mantener sesión"
- Link "¿Olvidaste tu contraseña?"
- Validación inline por campo

**RegisterForm:**
- Botón OAuth Google (UI lista, flujo pendiente)
- Campos: nombre, email, contraseña, confirmar contraseña
- Indicador de fortaleza de contraseña (3 criterios: 8+ chars, mayúscula, número)
- Checkbox aceptar términos y condiciones
- Validación inline por campo

---

## 10. Panel de administración

Accesible en `/admin`. Requiere rol `admin`. Al cerrar sesión se ejecuta `window.location.href = '/'` para limpiar el historial del navegador y evitar que el botón "Atrás" regrese al panel.

### AdminLayout
- Sidebar de 220 px colapsable a 64 px con tooltips en modo colapsado
- Topbar con nombre del usuario y botón de notificaciones
- Drawer en mobile
- Logout limpia el historial completo del SPA

### AdminDashboard (`/admin`)
- 4 métricas: pedidos del mes, ingresos COP, productos activos, clientes
- 3 alertas con semáforo de colores
- Gráfica de área de ventas por mes (`AreaChart` de Recharts)
- Top 4 productos por unidades vendidas
- Tabla de pedidos recientes

### AdminProductos (`/admin/productos`)
CRUD completo de productos.

**Tabla:**
- Búsqueda por nombre y filtro por categoría
- Thumbnail de imagen principal
- Conteo de fotos por producto
- Toggle activo/inactivo inline

**Modal crear/editar** — formulario único con dos secciones:

*Datos del producto:* nombre, categoría, precio m², descripción, toggle visible en tienda.

*Sección de imágenes con dos tabs:*
- **Subir desde dispositivo** — zona de clic o arrastre, selección múltiple, preview local inmediato y subida a Cloudinary en segundo plano
- **Pegar URL** — campo de texto con validación de URL de imagen

*Galería de fotos:* controles al hacer hover sobre cada foto — ⭐ marcar como principal · 🗑 eliminar. La imagen principal se indica con badge verde y borde destacado. Máximo 8 fotos por producto.

### AdminPedidos (`/admin/pedidos`)
- Tabla con búsqueda y filtro por estado
- `StatusSelect` con color dinámico por estado
- Modal de detalle: ítems con medidas, área m², precio/m² y total del pedido
- Cambio de estado disponible tanto en la tabla como en el modal

### AdminUsuarios (`/admin/usuarios`)
- 4 mini-estadísticas: total, activos, admins, clientes
- Tabla con avatar, rol con ícono, badge de proveedor de auth (Local / Google / Microsoft)
- Toggle activar/desactivar (bloqueado para cuentas con rol admin)

---

## 11. Integración local

El frontend envía sus solicitudes al gateway definido por `VITE_API_URL` en el
`.env` local; desde allí se enrutan a identidad, catálogo, carrito, pedidos,
notificaciones, facturación y pagos simulados. Las credenciales de servicios y
de base de datos se mantienen fuera del repositorio, en la configuración local
protegida de Windows.

---

## 12. Paleta de colores

Definida en `src/styles/globals.css` como variables CSS:

| Variable | Hex | Uso |
|----------|-----|-----|
| `--black` | `#000000` | Fondo principal |
| `--willow-green` | `#8fc263` | Acento principal, botones, precios |
| `--lime-cream` | `#cfe795` | Hover, estados activos |
| `--cornsilk` | `#f7efd3` | Texto principal |
| — | `#0d0d0d` | Superficies — cards, modales |
| — | `#080808` | Secciones alternadas |
| — | `rgba(143,194,99,0.12)` | Bordes sutiles |

---

## 13. Decisiones técnicas importantes

**`vite.config.js`** — no agregar `css.modules.localsConvention`. Rompe CSS Modules devolviendo objetos vacíos `{}`.

```js
// ✅ Correcto
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
export default defineConfig({ plugins: [react()] })
```

**Logout desde el panel admin** — se usa `window.location.href = '/'` en lugar de `navigate()` de React Router. Esto hace una recarga completa que borra el historial acumulado del panel, evitando que el botón "Atrás" regrese a rutas protegidas después de cerrar sesión.

**CarritoItems en cart-service** — los campos `ancho_cm` y `alto_cm` se envían en **milímetros enteros** (`valor_cm * 10`) por el índice único de la tabla `CarritoItems` en base de datos. En la lectura se divide entre 10 para mostrar en cm al usuario. El cálculo de `area_m2` no cambia visualmente.

**`react-is`** — dependencia peer de `recharts`, debe instalarse explícitamente o el panel admin falla al renderizar las gráficas:
```bash
yarn add react-is
```

---

## 14. Validación local

Con el frontend, el gateway y los siete servicios iniciados localmente, ejecuta
`.\run-e2e-local.ps1`. El script crea un administrador temporal, corre las
pruebas Playwright de persistencia del carrito, checkout aprobado/rechazado y
exclusión de pedidos rechazados en administración, envío del formulario y
cierre del carrito, y elimina los datos asociados a esa ejecución.
Para ejecutar solo algunos recorridos, pasa sus archivos con
`.\run-e2e-local.ps1 -TestFiles @("e2e\contact-form.spec.js","e2e\customer-cart-persistence.spec.js")`.
Las pruebas de checkout crean pedidos y, con SMTP real activado, generan correos
reales; para pruebas automatizadas, configura un motor de correo de consola.

`npm run lint` y `npm run build` validan el frontend de forma independiente.
El servicio de notificaciones requiere SMTP configurado para entregar los
mensajes de contacto y los avisos de pedidos al administrador y al cliente.