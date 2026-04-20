import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../context/AuthContext'
import { Search, Users, UserCheck, ShieldCheck, ChevronLeft, ChevronRight } from 'lucide-react'
import styles from './AdminUsuarios.module.css'

const API = import.meta.env.VITE_API_URL

const BADGE_PROVEEDOR = {
  local:     { label: 'Local',     color: '#6b7280' },
  google:    { label: 'Google',    color: '#ea4335' },
  microsoft: { label: 'Microsoft', color: '#0078d4' },
}

function Avatar({ nombre }) {
  const letra = nombre?.[0]?.toUpperCase() ?? '?'
  return <div className={styles.avatar}>{letra}</div>
}

export default function AdminUsuarios() {
  const { token } = useAuth()
  const [usuarios,  setUsuarios]  = useState([])
  const [stats,     setStats]     = useState({ total: 0, activos: 0, admins: 0, clientes: 0 })
  const [loading,   setLoading]   = useState(true)
  const [search,    setSearch]    = useState('')
  const [filtroRol, setFiltroRol] = useState('')
  const [page,      setPage]      = useState(1)
  const [pages,     setPages]     = useState(1)
  const [total,     setTotal]     = useState(0)
  const [toggling,  setToggling]  = useState(null)  // usuario_id en proceso

  const cargar = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({ page })
      if (search)    params.set('search', search)
      if (filtroRol) params.set('rol', filtroRol)
      const res  = await fetch(`${API}/admin/usuarios/?${params}`, { headers: { Authorization: `Bearer ${token}` } })
      const data = await res.json()
      setUsuarios(data.usuarios ?? [])
      setStats(data.stats ?? { total: 0, activos: 0, admins: 0, clientes: 0 })
      setPages(data.pages ?? 1)
      setTotal(data.total ?? 0)
    } catch { setUsuarios([]) }
    finally  { setLoading(false) }
  }, [token, page, search, filtroRol])

  useEffect(() => { cargar() }, [cargar])

  const toggleActivo = async (usuario) => {
    if (usuario.rol === 'admin') return   // protección
    setToggling(usuario.usuario_id)
    try {
      const res = await fetch(`${API}/admin/usuarios/${usuario.usuario_id}/activo/`, {
        method:  'PATCH',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body:    JSON.stringify({ activo: !usuario.activo }),
      })
      if (!res.ok) throw new Error()
      setUsuarios(us => us.map(u =>
        u.usuario_id === usuario.usuario_id ? { ...u, activo: !u.activo } : u
      ))
    } catch { alert('Error al actualizar el usuario') }
    finally { setToggling(null) }
  }

  return (
    <div className={styles.container}>
      {/* Stats */}
      <div className={styles.statsRow}>
        <div className={styles.statCard}>
          <Users size={20} />
          <div><strong>{stats.total}</strong><span>Total</span></div>
        </div>
        <div className={styles.statCard}>
          <UserCheck size={20} />
          <div><strong>{stats.activos}</strong><span>Activos</span></div>
        </div>
        <div className={styles.statCard} style={{ '--c': '#8fc263' }}>
          <ShieldCheck size={20} />
          <div><strong>{stats.admins}</strong><span>Admins</span></div>
        </div>
        <div className={styles.statCard}>
          <Users size={20} />
          <div><strong>{stats.clientes}</strong><span>Clientes</span></div>
        </div>
      </div>

      {/* Filtros */}
      <div className={styles.header}>
        <h2>Usuarios <span className={styles.count}>{total}</span></h2>
        <div className={styles.filtros}>
          <div className={styles.searchBox}>
            <Search size={16} />
            <input
              placeholder="Buscar nombre o email…"
              value={search}
              onChange={e => { setSearch(e.target.value); setPage(1) }}
            />
          </div>
          <select
            value={filtroRol}
            onChange={e => { setFiltroRol(e.target.value); setPage(1) }}
          >
            <option value="">Todos los roles</option>
            <option value="admin">Admin</option>
            <option value="cliente">Cliente</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className={styles.loadingWrap}><div className={styles.spinner} /></div>
      ) : (
        <>
          <div className={styles.tableWrap}>
            <table className={styles.tabla}>
              <thead>
                <tr>
                  <th>Usuario</th><th>Rol</th><th>Proveedor</th>
                  <th>Registro</th><th>Activo</th>
                </tr>
              </thead>
              <tbody>
                {usuarios.length === 0 ? (
                  <tr><td colSpan={5} className={styles.empty}>Sin resultados</td></tr>
                ) : usuarios.map(u => (
                  <tr key={u.usuario_id}>
                    <td>
                      <div className={styles.userCell}>
                        <Avatar nombre={u.nombre} />
                        <div>
                          <strong>{u.nombre}</strong>
                          <span>{u.email}</span>
                        </div>
                      </div>
                    </td>
                    <td>
                      <span className={`${styles.rolBadge} ${u.rol === 'admin' ? styles.rolAdmin : styles.rolCliente}`}>
                        {u.rol === 'admin' ? <ShieldCheck size={12} /> : <Users size={12} />}
                        {u.rol}
                      </span>
                    </td>
                    <td>
                      <span
                        className={styles.proveedorBadge}
                        style={{ background: `${BADGE_PROVEEDOR[u.proveedor_auth]?.color ?? '#555'}22`,
                                 color:      BADGE_PROVEEDOR[u.proveedor_auth]?.color ?? '#aaa',
                                 borderColor: `${BADGE_PROVEEDOR[u.proveedor_auth]?.color ?? '#555'}55` }}
                      >
                        {BADGE_PROVEEDOR[u.proveedor_auth]?.label ?? u.proveedor_auth}
                      </span>
                    </td>
                    <td>{new Date(u.fecha_registro).toLocaleDateString('es-CO')}</td>
                    <td>
                      <button
                        className={`${styles.toggle} ${u.activo ? styles.toggleOn : styles.toggleOff}`}
                        disabled={u.rol === 'admin' || toggling === u.usuario_id}
                        onClick={() => toggleActivo(u)}
                        title={u.rol === 'admin' ? 'No se puede desactivar un admin' : (u.activo ? 'Desactivar' : 'Activar')}
                      >
                        <span className={styles.toggleKnob} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {pages > 1 && (
            <div className={styles.paginacion}>
              <button disabled={page <= 1}    onClick={() => setPage(p => p - 1)}><ChevronLeft  size={16} /></button>
              <span>Página {page} de {pages}</span>
              <button disabled={page >= pages} onClick={() => setPage(p => p + 1)}><ChevronRight size={16} /></button>
            </div>
          )}
        </>
      )}
    </div>
  )
}