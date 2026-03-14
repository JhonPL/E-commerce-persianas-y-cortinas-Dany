import { useState } from 'react'
import { Search, X, ShieldCheck, User, ToggleLeft, ToggleRight } from 'lucide-react'
import styles from './AdminUsuarios.module.css'

const INITIAL = [
  { id: 1, nombre: 'Administrador Dany', email: 'admin@cortinasydany.com', rol: 'admin',   auth: 'local',    activo: true,  fecha: '2026-01-15' },
  { id: 2, nombre: 'María Pérez',        email: 'maria.perez@example.com', rol: 'cliente',  auth: 'local',    activo: true,  fecha: '2026-02-03' },
  { id: 3, nombre: 'Carlos Rodríguez',   email: 'carlos.rodriguez@example.com', rol: 'cliente', auth: 'local', activo: true, fecha: '2026-02-10' },
  { id: 4, nombre: 'Laura Gómez',        email: 'laura.gomez@gmail.com',   rol: 'cliente',  auth: 'google',   activo: true,  fecha: '2026-02-18' },
  { id: 5, nombre: 'Jorge Martínez',     email: 'jorge.m@example.com',     rol: 'cliente',  auth: 'local',    activo: true,  fecha: '2026-03-01' },
  { id: 6, nombre: 'Ana Torres',         email: 'ana.torres@example.com',  rol: 'cliente',  auth: 'local',    activo: false, fecha: '2026-03-05' },
]

const AUTH_STYLE = {
  local:     { label: 'Local',  bg: 'rgba(143,194,99,0.1)',  color: '#8fc263' },
  google:    { label: 'Google', bg: 'rgba(66,133,244,0.12)', color: '#4285F4' },
  microsoft: { label: 'Microsoft', bg: 'rgba(0,114,198,0.12)', color: '#0072C6' },
}

export default function AdminUsuarios() {
  const [usuarios, setUsuarios] = useState(INITIAL)
  const [search, setSearch]     = useState('')
  const [filter, setFilter]     = useState('Todos')

  const filtered = usuarios.filter(u => {
    const matchS = u.nombre.toLowerCase().includes(search.toLowerCase()) ||
                   u.email.toLowerCase().includes(search.toLowerCase())
    const matchF = filter === 'Todos'
      ? true : filter === 'Activos'
      ? u.activo : filter === 'Inactivos'
      ? !u.activo : u.rol === filter
    return matchS && matchF
  })

  const toggleActivo = (id) => {
    setUsuarios(prev => prev.map(u => u.id === id ? { ...u, activo: !u.activo } : u))
  }

  const totales = {
    total: usuarios.length,
    activos: usuarios.filter(u => u.activo).length,
    admin: usuarios.filter(u => u.rol === 'admin').length,
    clientes: usuarios.filter(u => u.rol === 'cliente').length,
  }

  return (
    <div className={styles.page}>

      <div className={styles.pageHeader}>
        <div>
          <h1 className={styles.pageTitle}>Usuarios</h1>
          <p className={styles.pageSub}>{totales.total} usuarios registrados</p>
        </div>
      </div>

      {/* Resumen rápido */}
      <div className={styles.statsRow}>
        {[
          { label: 'Total',    value: totales.total    },
          { label: 'Activos',  value: totales.activos  },
          { label: 'Admins',   value: totales.admin    },
          { label: 'Clientes', value: totales.clientes },
        ].map(s => (
          <div key={s.label} className={styles.statCard}>
            <span className={styles.statValue}>{s.value}</span>
            <span className={styles.statLabel}>{s.label}</span>
          </div>
        ))}
      </div>

      {/* Filtros */}
      <div className={styles.filters}>
        <div className={styles.searchWrapper}>
          <Search size={15} className={styles.searchIcon} />
          <input type="text" placeholder="Buscar por nombre o correo..."
            value={search} onChange={e => setSearch(e.target.value)}
            className={styles.searchInput} />
          {search && <button className={styles.clearSearch} onClick={() => setSearch('')}><X size={14} /></button>}
        </div>
        <div className={styles.pills}>
          {['Todos','Activos','Inactivos','admin','cliente'].map(f => (
            <button key={f}
              className={`${styles.pill} ${filter === f ? styles.pillActive : ''}`}
              onClick={() => setFilter(f)}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Tabla */}
      <div className={styles.tableCard}>
        <div className={styles.tableWrapper}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Usuario</th>
                <th>Rol</th>
                <th>Auth</th>
                <th>Registro</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 && (
                <tr><td colSpan={5} className={styles.empty}>Sin resultados</td></tr>
              )}
              {filtered.map(u => (
                <tr key={u.id}>
                  <td>
                    <div className={styles.userCell}>
                      <div className={`${styles.avatar} ${u.rol === 'admin' ? styles.avatarAdmin : ''}`}>
                        {u.nombre.charAt(0).toUpperCase()}
                      </div>
                      <div className={styles.userInfo}>
                        <span className={styles.userName}>{u.nombre}</span>
                        <span className={styles.userEmail}>{u.email}</span>
                      </div>
                    </div>
                  </td>
                  <td>
                    <span className={`${styles.rolBadge} ${u.rol === 'admin' ? styles.rolAdmin : styles.rolCliente}`}>
                      {u.rol === 'admin' ? <ShieldCheck size={11} /> : <User size={11} />}
                      {u.rol}
                    </span>
                  </td>
                  <td>
                    <span
                      className={styles.authBadge}
                      style={{ background: AUTH_STYLE[u.auth]?.bg, color: AUTH_STYLE[u.auth]?.color }}
                    >
                      {AUTH_STYLE[u.auth]?.label}
                    </span>
                  </td>
                  <td className={styles.tdMuted}>{u.fecha}</td>
                  <td>
                    <button
                      className={styles.toggleBtn}
                      onClick={() => u.rol !== 'admin' && toggleActivo(u.id)}
                      disabled={u.rol === 'admin'}
                      title={u.rol === 'admin' ? 'No se puede desactivar al admin' : u.activo ? 'Desactivar' : 'Activar'}
                    >
                      {u.activo
                        ? <><ToggleRight size={20} color="#8fc263" /><span className={styles.toggleOn}>Activo</span></>
                        : <><ToggleLeft  size={20} color="#555"    /><span className={styles.toggleOff}>Inactivo</span></>
                      }
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}