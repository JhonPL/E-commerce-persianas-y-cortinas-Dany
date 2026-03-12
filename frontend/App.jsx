import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { CartProvider } from './context/CartContext'
import { AuthProvider, useAuth } from './context/AuthContext'
import Navbar from './components/Navbar/Navbar'
import WhatsAppButton from './components/WhatsAppButton/WhatsAppButton'
import Footer from './components/Footer/Footer'
import CartDrawer from './components/CartDrawer/CartDrawer'
import Home from './pages/Home/Home'
import Tienda from './pages/Tienda/Tienda'
import Detalle from './pages/Detalle/Detalle'
import Contacto from './pages/Contacto/Contacto'
import MisPedidos from './pages/Mispedidos/MisPedidos'
import Auth from './Auth/Auth'
import AdminLayout from './Admin/AdminLayout'
import AdminDashboard from './Admin/AdminDashboard'
import AdminProductos from './Admin/AdminProductos'
import AdminPedidos from './Admin/AdminPedidos'
import AdminUsuarios from './Admin/AdminUsuarios'
import NotFound from './pages/NotFound/NotFound'
import './styles/globals.css'

// Ruta protegida: requiere sesión activa
function RequireAuth({ children }) {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" state={{ from: window.location.pathname }} replace />
  return children
}

function RequireAdmin({ children }) {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
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
      <AuthProvider>
        <CartProvider>
          <Routes>

            {/* Tienda pública */}
            <Route path="/"             element={<Layout><Home     /></Layout>} />
            <Route path="/tienda"       element={<Layout><Tienda   /></Layout>} />
            <Route path="/producto/:id" element={<Layout><Detalle  /></Layout>} />
            <Route path="/contacto"     element={<Layout><Contacto /></Layout>} />

            {/* Requiere sesión */}
            <Route path="/mis-pedidos" element={
              <RequireAuth><Layout><MisPedidos /></Layout></RequireAuth>
            } />

            {/* Auth */}
            <Route path="/login" element={<Auth />} />

            {/* Panel admin */}
            <Route path="/admin" element={
              <RequireAdmin><AdminLayout /></RequireAdmin>
            }>
              <Route index              element={<AdminDashboard />} />
              <Route path="productos"   element={<AdminProductos />} />
              <Route path="pedidos"     element={<AdminPedidos   />} />
              <Route path="usuarios"    element={<AdminUsuarios  />} />
            </Route>

            {/* 404 */}
            <Route path="*" element={<Layout><NotFound /></Layout>} />

          </Routes>
        </CartProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}