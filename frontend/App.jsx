import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { CartProvider } from './src/context/CartContext'
import { AuthProvider, useAuth } from './src/context/AuthContext'
import Navbar from './src/components/Navbar/Navbar'
import WhatsAppButton from './src/components/WhatsAppButton/WhatsAppButton'
import Footer from './src/components/Footer/Footer'
import CartDrawer from './src/components/CartDrawer/CartDrawer'
import Home from './src/pages/Home/Home'
import Tienda from './src/pages/Tienda/Tienda'
import Detalle from './src/pages/Detalle/Detalle'
import Contacto from './src/pages/Contacto/Contacto'
import MisPedidos from './src/pages/MisPedidos/MisPedidos'
import Auth from './src/Auth/Auth'
import AdminLayout from './src/Admin/AdminLayout'
import AdminDashboard from './src/Admin/AdminDashboard'
import AdminProductos from './src/Admin/AdminProductos'
import AdminPedidos from './src/Admin/AdminPedidos'
import AdminUsuarios from './src/Admin/AdminUsuarios'
import NotFound from './src/pages/NotFound/NotFound'
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