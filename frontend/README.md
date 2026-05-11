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

> **Actualmente:** `login` y `register` usan mocks con 800 ms de delay simulado. Ver sección [Pendientes](#14-pendientes--conexión-con-backend).

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
- Botón de WhatsApp directo
- Mapa embed de Google Maps (Villavicencio)
- Formulario con validación y estado de éxito
- **TODO:** conectar a `POST /api/contacto`

### MisPedidos (`/mis-pedidos`) — RequireAuth
Historial de pedidos del cliente autenticado:
- Cards colapsables por pedido con barra de progreso de 3 estados
- Tabla de ítems con medidas y precios
- Estado vacío con enlace a la tienda
- **TODO:** conectar a `GET /api/mis-pedidos`

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

## 11. Usuarios mock para desarrollo

Mientras no esté conectado el backend, `AuthContext` simula la autenticación con estos datos:

| Email | Contraseña | Rol | Acceso |
|-------|-----------|-----|--------|
| `admin@cortinasydany.com` | `Admin2024$` | admin | Panel administrador |
| Cualquier email válido | `Cliente123$` | cliente | Tienda + Mis Pedidos |

> El registro también funciona en mock — crea un usuario cliente temporal en memoria que se pierde al recargar la página.

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

**CarritoItems en backend** — cuando se conecte el backend, los campos `ancho_cm` y `alto_cm` se deben enviar en **milímetros enteros** (`valor_cm * 10`) por el índice único de la tabla `CarritoItems` en base de datos. En la lectura se divide entre 10 para mostrar en cm al usuario. El cálculo de `area_m2` no cambia visualmente.

**`react-is`** — dependencia peer de `recharts`, debe instalarse explícitamente o el panel admin falla al renderizar las gráficas:
```bash
yarn add react-is
```

---

## 14. Pendientes — Conexión con backend

Todos los puntos de integración tienen un comentario `// TODO` en el código fuente.

| Archivo | Función / sección | Endpoint esperado |
|---------|------------------|-------------------|
| `AuthContext.jsx` | `login()` | `POST /api/auth/login` |
| `AuthContext.jsx` | `register()` | `POST /api/auth/register` |
| `AuthContext.jsx` | OAuth Google | `GET /api/auth/google` |
| `MisPedidos.jsx` | carga de pedidos | `GET /api/mis-pedidos` |
| `Contacto.jsx` | envío formulario | `POST /api/contacto` |
| `AdminProductos.jsx` | listar productos | `GET /api/admin/productos` |
| `AdminProductos.jsx` | crear producto | `POST /api/admin/productos` |
| `AdminProductos.jsx` | editar producto | `PUT /api/admin/productos/:id` |
| `AdminProductos.jsx` | eliminar producto | `DELETE /api/admin/productos/:id` |
| `AdminPedidos.jsx` | listar pedidos | `GET /api/admin/pedidos` |
| `AdminPedidos.jsx` | cambiar estado | `PATCH /api/admin/pedidos/:id/estado` |
| `AdminUsuarios.jsx` | listar usuarios | `GET /api/admin/usuarios` |
| `AdminUsuarios.jsx` | activar/desactivar | `PATCH /api/admin/usuarios/:id/activo` |
| `Tienda.jsx` / `Home.jsx` | catálogo público | `GET /api/productos` |
| `Detalle.jsx` | detalle producto | `GET /api/productos/:id` |
| `CartDrawer.jsx` | ir a checkout | `POST /api/checkout` *(página pendiente)* |