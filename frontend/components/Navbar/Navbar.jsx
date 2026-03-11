import { useState, useEffect } from 'react'
import { Link, NavLink, useLocation } from 'react-router-dom'
import { ShoppingCart, User, Search, Menu, X } from 'lucide-react'
import { useCart } from '../../context/CartContext'
import CartDrawer from '../CartDrawer/CartDrawer'
import styles from './Navbar.module.css'
console.log('STYLES:', styles)

export default function Navbar() {
  const { count, toggleCart } = useCart()
  const [scrolled, setScrolled]   = useState(false)
  const [menuOpen, setMenuOpen]   = useState(false)
  const [searchOpen, setSearchOpen] = useState(false)
  const location = useLocation()

  // Detectar scroll para cambiar fondo
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  // Cerrar menú al cambiar de ruta
  useEffect(() => { setMenuOpen(false) }, [location])

  return (
    <>
      <header className={`${styles.navbar} ${scrolled ? styles.scrolled : ''}`}>
        <div className={styles.inner}>

          {/* Logo */}
          <Link to="/" className={styles.logo}>
            <span className={styles.logoIcon}>🪟</span>
            <div className={styles.logoText}>
              <span className={styles.logoTop}>PERSIANAS &amp; CORTINAS</span>
              <span className={styles.logoBottom}>DANY</span>
            </div>
          </Link>

          {/* Nav central */}
          <nav className={`${styles.nav} ${menuOpen ? styles.navOpen : ''}`}>
            <NavLink to="/"       className={({ isActive }) => isActive ? `${styles.link} ${styles.active}` : styles.link}>Inicio</NavLink>
            <NavLink to="/tienda" className={({ isActive }) => isActive ? `${styles.link} ${styles.active}` : styles.link}>Tienda</NavLink>
            <NavLink to="/contacto" className={({ isActive }) => isActive ? `${styles.link} ${styles.active}` : styles.link}>Contacto</NavLink>
          </nav>

          {/* Acciones */}
          <div className={styles.actions}>
            <button className={styles.iconBtn} onClick={() => setSearchOpen(v => !v)} aria-label="Buscar">
              <Search size={18} />
            </button>
            <Link to="/login" className={styles.iconBtn} aria-label="Entrar">
              <User size={18} />
              <span className={styles.iconLabel}>Entrar</span>
            </Link>
            <button className={styles.iconBtn} onClick={toggleCart} aria-label="Carrito">
              <ShoppingCart size={18} />
              {count > 0 && <span className={styles.badge}>{count}</span>}
            </button>
            <button className={styles.hamburger} onClick={() => setMenuOpen(v => !v)} aria-label="Menú">
              {menuOpen ? <X size={22} /> : <Menu size={22} />}
            </button>
          </div>
        </div>

        {/* Barra de búsqueda expandible */}
        {searchOpen && (
          <div className={styles.searchBar}>
            <input
              autoFocus
              type="text"
              placeholder="Buscar productos..."
              className={styles.searchInput}
              onKeyDown={(e) => e.key === 'Escape' && setSearchOpen(false)}
            />
          </div>
        )}
      </header>

      <CartDrawer />
    </>
  )
}