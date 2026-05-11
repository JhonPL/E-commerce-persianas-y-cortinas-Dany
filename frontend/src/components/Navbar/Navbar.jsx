import { useState, useEffect, useRef } from 'react'
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { ShoppingCart, User, Search, Menu, X, LogOut, ChevronDown } from 'lucide-react'
import { useCart } from '../../context/CartContext'
import { useAuth } from '../../context/AuthContext'
import styles from './Navbar.module.css'

export default function Navbar() {
  const { count, toggleCart } = useCart()
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [scrolled,    setScrolled]    = useState(false)
  const [menuOpen,    setMenuOpen]    = useState(false)
  const [searchOpen,  setSearchOpen]  = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const location = useLocation()
  const userMenuRef = useRef(null)

  // Maneja logout y navega a tienda sin agregar al historial
  const handleLogout = () => {
    logout()
    navigate('/tienda', { replace: true })
  }

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  // Cierra menús al cambiar de ruta
  useEffect(() => { setMenuOpen(false); setUserMenuOpen(false) }, [location])

  // Cierra dropdown de usuario al clicar afuera
  useEffect(() => {
    const handler = (e) => {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target)) {
        setUserMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  return (
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

        {/* Nav */}
        <nav className={`${styles.nav} ${menuOpen ? styles.navOpen : ''}`}>
          <NavLink to="/"       className={({ isActive }) => `${styles.link} ${isActive ? styles.active : ''}`}>Inicio</NavLink>
          <NavLink to="/tienda" className={({ isActive }) => `${styles.link} ${isActive ? styles.active : ''}`}>Tienda</NavLink>
          <NavLink to="/contacto" className={({ isActive }) => `${styles.link} ${isActive ? styles.active : ''}`}>Contacto</NavLink>
        </nav>

        {/* Actions */}
        <div className={styles.actions}>

          {/* Buscador */}
          <button
            className={styles.iconBtn}
            onClick={() => setSearchOpen(v => !v)}
            aria-label="Buscar"
          >
            <Search size={18} />
          </button>

          {/* Usuario: si tiene sesión → avatar + dropdown, si no → botón Entrar */}
          {user ? (
            <div className={styles.userMenu} ref={userMenuRef}>
              <button
                className={styles.userBtn}
                onClick={() => setUserMenuOpen(v => !v)}
                aria-label="Mi cuenta"
              >
                <span className={styles.userAvatar}>
                  {user.nombre.charAt(0).toUpperCase()}
                </span>
                <span className={styles.iconLabel}>{user.nombre.split(' ')[0]}</span>
                <ChevronDown size={13} className={`${styles.chevron} ${userMenuOpen ? styles.chevronOpen : ''}`} />
              </button>

              {userMenuOpen && (
                <div className={styles.userDropdown}>
                  <div className={styles.userDropdownHeader}>
                    <span className={styles.userDropdownName}>{user.nombre}</span>
                    <span className={styles.userDropdownEmail}>{user.email}</span>
                  </div>
                  <div className={styles.userDropdownDivider} />
                  {user.rol === 'admin' && (
                    <Link to="/admin" className={styles.userDropdownItem}>
                      Panel admin
                    </Link>
                  )}
                  <Link to="/mis-pedidos" className={styles.userDropdownItem}>
                    Mis pedidos
                  </Link>
                  <div className={styles.userDropdownDivider} />
                  <button
                    className={`${styles.userDropdownItem} ${styles.userDropdownLogout}`}
                    onClick={handleLogout}
                  >
                    <LogOut size={14} />
                    Cerrar sesión
                  </button>
                </div>
              )}
            </div>
          ) : (
            <Link to="/login" className={styles.iconBtn} aria-label="Entrar">
              <User size={18} />
              <span className={styles.iconLabel}>Entrar</span>
            </Link>
          )}

          {/* Carrito */}
          <button className={styles.iconBtn} onClick={toggleCart} aria-label="Carrito">
            <ShoppingCart size={18} />
            {count > 0 && <span className={styles.badge}>{count}</span>}
          </button>

          {/* Hamburger */}
          <button
            className={styles.hamburger}
            onClick={() => setMenuOpen(v => !v)}
            aria-label="Menú"
          >
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
  )
}