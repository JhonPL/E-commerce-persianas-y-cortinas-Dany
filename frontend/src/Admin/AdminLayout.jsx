import { useState } from 'react'
import { NavLink, useNavigate, Outlet } from 'react-router-dom'
import {
  LayoutDashboard, Package, ShoppingBag, Users,
  ChevronLeft, ChevronRight, LogOut, Menu, Bell, X
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import styles from './Admin.module.css'

const NAV = [
  { to: '/admin',           icon: LayoutDashboard, label: 'Dashboard',  end: true },
  { to: '/admin/productos', icon: Package,          label: 'Productos'  },
  { to: '/admin/pedidos',   icon: ShoppingBag,      label: 'Pedidos'    },
  { to: '/admin/usuarios',  icon: Users,            label: 'Usuarios'   },
]

export default function AdminLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  const handleLogout = () => { 
    logout()
    window.history.replaceState(null, '', '/')
    navigate('/login')
  }

  return (
    <div className={styles.shell}>

      {/* ── Backdrop mobile ─────────────────────────────── */}
      {mobileOpen && (
        <div className={styles.backdrop} onClick={() => setMobileOpen(false)} />
      )}

      {/* ── Sidebar ─────────────────────────────────────── */}
      <aside className={`${styles.sidebar} ${collapsed ? styles.sidebarCollapsed : ''} ${mobileOpen ? styles.sidebarMobileOpen : ''}`}>

        {/* Header sidebar */}
        <div className={styles.sidebarHeader}>
          {!collapsed && (
            <div className={styles.sidebarLogo}>
              <span className={styles.sidebarLogoIcon}>🪟</span>
              <div className={styles.sidebarLogoText}>
                <span className={styles.sidebarLogoName}>DANY</span>
                <span className={styles.sidebarLogoSub}>Panel Admin</span>
              </div>
            </div>
          )}
          {collapsed && <span className={styles.sidebarLogoIconOnly}>🪟</span>}
          <button
            className={styles.collapseBtn}
            onClick={() => setCollapsed(v => !v)}
            aria-label="Colapsar menú"
          >
            {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          </button>
        </div>

        {/* Nav links */}
        <nav className={styles.sidebarNav}>
          {NAV.map(({ to, icon: Icon, label, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `${styles.navItem} ${isActive ? styles.navItemActive : ''}`
              }
              title={collapsed ? label : undefined}
            >
              <Icon size={18} className={styles.navIcon} />
              {!collapsed && <span className={styles.navLabel}>{label}</span>}
              {collapsed && <span className={styles.navTooltip}>{label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* Footer sidebar */}
        <div className={styles.sidebarFooter}>
          {!collapsed && (
            <div className={styles.sidebarUser}>
              <span className={styles.sidebarAvatar}>
                {user?.nombre?.charAt(0).toUpperCase()}
              </span>
              <div className={styles.sidebarUserInfo}>
                <span className={styles.sidebarUserName}>{user?.nombre?.split(' ')[0]}</span>
                <span className={styles.sidebarUserRole}>Administrador</span>
              </div>
            </div>
          )}
          <button className={styles.logoutBtn} onClick={handleLogout} title="Cerrar sesión">
            <LogOut size={16} />
            {!collapsed && <span>Salir</span>}
          </button>
        </div>
      </aside>

      {/* ── Main ────────────────────────────────────────── */}
      <div className={`${styles.main} ${collapsed ? styles.mainExpanded : ''}`}>

        {/* Topbar */}
        <header className={styles.topbar}>
          <button
            className={styles.mobileMenuBtn}
            onClick={() => setMobileOpen(v => !v)}
          >
            {mobileOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
          <div className={styles.topbarRight}>
            <button className={styles.topbarIconBtn} aria-label="Notificaciones">
              <Bell size={18} />
              <span className={styles.notifDot} />
            </button>
            <div className={styles.topbarUser}>
              <span className={styles.topbarAvatar}>
                {user?.nombre?.charAt(0).toUpperCase()}
              </span>
              <span className={styles.topbarUserName}>{user?.nombre}</span>
            </div>
          </div>
        </header>

        {/* Contenido de cada sub-página */}
        <main className={styles.content}>
          <Outlet />
        </main>
      </div>
    </div>
  )
}