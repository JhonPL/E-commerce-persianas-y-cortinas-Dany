import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { CartProvider } from './context/CartContext'
import Navbar from './components/Navbar/Navbar'
import Footer from './components/Footer/Footer'
import WhatsAppButton from './components/WhatsAppButton/WhatsAppButton'
import Home from './pages/Home/Home'
import Tienda from './pages/Tienda/Tienda'
import Detalle from './pages/Detalle/Detalle'
import './styles/globals.css'

export default function App() {
  return (
    <BrowserRouter>
      <CartProvider>
        <Navbar />
        <main>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/tienda" element={<Tienda />} />
            <Route path="/producto/:id" element={<Detalle />} />
          </Routes>
        </main>
        <Footer />
        <WhatsAppButton phoneNumber="573123558218" />
      </CartProvider>
    </BrowserRouter>
  )
}