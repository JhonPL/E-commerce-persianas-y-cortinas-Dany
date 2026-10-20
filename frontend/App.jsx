import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { CartProvider } from './src/context/CartContext'
import { AuthProvider, useAuth } from './src/context/AuthContext'
import ScrollToTop from './src/components/ScrollToTop'
import Navbar from './src/components/Navbar/Navbar'
import WhatsAppButton from './src/components/WhatsAppButton/WhatsAppButton'
import Footer from './src/components/Footer/Footer'
import CartDrawer from './src/components/CartDrawer/CartDrawer'
import Home from './src/pages/Home/Home'
import './styles/globals.css'

const Tienda = lazy(() => import('./src/pages/Tienda/Tienda'))
const Detalle = lazy(() => import('./src/pages/Detalle/Detalle'))
const Contacto = lazy(() => import('./src/pages/Contacto/Contacto'))
const MisPedidos = lazy(() => import('./src/pages/MisPedidos/MisPedidos'))
const Checkout = lazy(() => import('./src/pages/Checkout/Checkout'))
const Auth = lazy(() => import('./src/Auth/Auth'))
const GoogleCallback = lazy(() => import('./src/Auth/GoogleCallback'))
const AdminLayout = lazy(() => import('./src/Admin/AdminLayout'))
const AdminDashboard = lazy(() => import('./src/Admin/AdminDashboard'))
const AdminProductos = lazy(() => import('./src/Admin/AdminProductos'))
const AdminPedidos = lazy(() => import('./src/Admin/AdminPedidos'))
const AdminUsuarios = lazy(() => import('./src/Admin/AdminUsuarios'))
const AdminCategorias = lazy(() => import('./src/Admin/Admincategorias'))
const NotFound = lazy(() => import('./src/pages/NotFound/NotFound'))

function LazyRoute({ children }) {
  return (
    <Suspense fallback={<main role="status" style={{ padding: '4rem 1rem', textAlign: 'center' }}>Cargando página…</main>}>
      {children}
    </Suspense>
  )
}

function RequireAuth({ children }) {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" state={{ from: window.location.pathname }} replace />
  return children
}
 
function RequireAdmin({ children }) {
  const { user } = useAuth()
  if (!user) return <Navigate to="/" replace />
  if (user.rol !== 'admin') return <Navigate to="/" replace />
  return children
}
 
function Layout({ children }) {
  return (
    <>
      <Navbar />
      <CartDrawer />
      {children}
      <WhatsAppButton />
      <Footer />
    </>
  )
}
 
export default function App() {
  return (
    <BrowserRouter>
      <ScrollToTop />
      <AuthProvider>
        <CartProvider>
          <Routes>
 
            {/* Tienda pública */}
            <Route path="/"             element={<Layout><Home     /></Layout>} />
            <Route path="/tienda"       element={<Layout><LazyRoute><Tienda /></LazyRoute></Layout>} />
            <Route path="/producto/:id" element={<Layout><LazyRoute><Detalle /></LazyRoute></Layout>} />
            <Route path="/contacto"     element={<Layout><LazyRoute><Contacto /></LazyRoute></Layout>} />
 
            {/* Requiere sesión */}
            <Route path="/mis-pedidos" element={
              <RequireAuth><Layout><LazyRoute><MisPedidos /></LazyRoute></Layout></RequireAuth>
            } />
            <Route path="/checkout" element={
              <RequireAuth><Layout><LazyRoute><Checkout /></LazyRoute></Layout></RequireAuth>
            } />
 
            {/* Auth */}
            <Route path="/login" element={<LazyRoute><Auth /></LazyRoute>} />
            <Route path="/oauth/google" element={<LazyRoute><GoogleCallback /></LazyRoute>} />
            
 
            {/* Panel admin */}
            <Route path="/admin" element={
              <RequireAdmin><LazyRoute><AdminLayout /></LazyRoute></RequireAdmin>
            }>
              <Route index              element={<LazyRoute><AdminDashboard /></LazyRoute>} />
              <Route path="productos"   element={<LazyRoute><AdminProductos /></LazyRoute>} />
              <Route path="categorias"  element={<LazyRoute><AdminCategorias /></LazyRoute>} />
              <Route path="pedidos"     element={<LazyRoute><AdminPedidos /></LazyRoute>} />
              <Route path="usuarios"    element={<LazyRoute><AdminUsuarios /></LazyRoute>} />
            </Route>
 
            {/* 404 */}
            <Route path="*" element={<Layout><LazyRoute><NotFound /></LazyRoute></Layout>} />
 
          </Routes>
        </CartProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}

