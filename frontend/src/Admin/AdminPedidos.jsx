import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../context/AuthContext'
import { Search, Eye, X, ChevronLeft, ChevronRight } from 'lucide-react'
import styles from './AdminPedidos.module.css'

const API = import.meta.env.VITE_API_URL

const COLOR_ESTADO = {
  'Pendiente de preparación': '#f59e0b',
  'Preparado':                '#3b82f6',
  'Enviado':                  '#8fc263',
}

function ModalDetalle({ pedido, estados, onCerrar, onCambiarEstado }) {
  const [estadoId, setEstadoId] = useState(pedido.estado_id)
  const [guardando, setGuardando] = useState(false)

  const cambiar = async () => {
    if (estadoId === pedido.estado_id) return
    setGuardando(true)
    await onCambiarEstado(pedido.pedido_id, estadoId)
    setGuardando(false)
  }

  return (
    <div className={styles.overlay} onClick={e => e.target === e.currentTarget && onCerrar()}>
      <div className={styles.modal}>
        <div className={styles.modalHeader}>
          <h3>Pedido #{pedido.pedido_id}</h3>
          <button onClick={onCerrar}><X size={18} /></button>
        </div>

        <div className={styles.modalBody}>
          {/* Info cliente */}
          <div className={styles.infoGrid}>
            <div><span>Cliente</span><strong>{pedido.cliente_nombre}</strong></div>
            <div><span>Email</span><strong>{pedido.cliente_email}</strong></div>
            <div><span>Ciudad</span><strong>{pedido.ciudad || '—'}</strong></div>
            <div><span>Fecha</span><strong>{new Date(pedido.fecha_pedido).toLocaleDateString('es-CO')}</strong></div>
          </div>

          {/* Cambio de estado */}
          <div className={styles.estadoRow}>
            <label>Estado del pedido</label>
            <select
              value={estadoId}
              onChange={e => setEstadoId(Number(e.target.value))}
              style={{ borderColor: COLOR_ESTADO[estados.find(e => e.estado_id === estadoId)?.nombre] }}
            >
              {estados.map(e => (
                <option key={e.estado_id} value={e.estado_id}>{e.nombre}</option>
              ))}
            </select>
            <button
              className={styles.btnGuardar}
              onClick={cambiar}
              disabled={guardando || estadoId === pedido.estado_id}
            >
              {guardando ? 'Guardando…' : 'Guardar'}
            </button>
          </div>

          {/* Tabla de ítems */}
          <table className={styles.tabla}>
            <thead>
              <tr><th>Producto</th><th>Medidas</th><th>Área</th><th>$/m²</th><th>Cant.</th><th>Total</th></tr>
            </thead>
            <tbody>
              {(pedido.detalles || []).map(d => (
                <tr key={d.detalle_id}>
                  <td>
                    <div className={styles.prodCell}>
                      {d.imagen_principal && <img src={d.imagen_principal} alt="" className={styles.thumb} />}
                      <span>{d.nombre}</span>
                    </div>
                  </td>
                  <td>{d.ancho_cm}×{d.alto_cm} cm</td>
                  <td>{parseFloat(d.area_m2).toFixed(2)} m²</td>
                  <td>${parseFloat(d.precio_m2).toLocaleString('es-CO')}</td>
                  <td>{d.cantidad}</td>
                  <td className={styles.tdTotal}>${parseFloat(d.precio_total).toLocaleString('es-CO')}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className={styles.totalRow}>
            <span>Total</span>
            <strong>${parseFloat(pedido.total).toLocaleString('es-CO')}</strong>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function AdminPedidos() {
  const { token } = useAuth()
  const [pedidos,   setPedidos]   = useState([])
  const [estados,   setEstados]   = useState([])
  const [loading,   setLoading]   = useState(true)
  const [search,    setSearch]    = useState('')
  const [filtroEst, setFiltroEst] = useState('')
  const [page,      setPage]      = useState(1)
  const [pages,     setPages]     = useState(1)
  const [total,     setTotal]     = useState(0)
  const [seleccionado, setSeleccionado] = useState(null)
  const [detalleCache, setDetalleCache] = useState({})

  const cargarEstados = useCallback(async () => {
    try {
      const res  = await fetch(`${API}/admin/estados-pedido/`, { headers: { Authorization: `Bearer ${token}` } })
      const data = await res.json()
      setEstados(data)
    } catch { /* silencioso */ }
  }, [token])

  const cargarPedidos = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({ page })
      if (search)    params.set('search', search)
      if (filtroEst) params.set('estado', filtroEst)
      const res  = await fetch(`${API}/admin/pedidos/?${params}`, { headers: { Authorization: `Bearer ${token}` } })
      const data = await res.json()
      setPedidos(data.pedidos ?? [])
      setPages(data.pages ?? 1)
      setTotal(data.total ?? 0)
    } catch { setPedidos([]) }
    finally  { setLoading(false) }
  }, [token, page, search, filtroEst])

  useEffect(() => { cargarEstados() }, [cargarEstados])
  useEffect(() => { cargarPedidos() }, [cargarPedidos])

  // Cargar detalle completo del pedido al abrir modal
  const abrirDetalle = async (pedido) => {
    if (detalleCache[pedido.pedido_id]) {
      setSeleccionado(detalleCache[pedido.pedido_id])
      return
    }
    try {
      const res  = await fetch(`${API}/pedidos/${pedido.pedido_id}/`, { headers: { Authorization: `Bearer ${token}` } })
      const data = await res.json()
      setDetalleCache(c => ({ ...c, [pedido.pedido_id]: data }))
      setSeleccionado(data)
    } catch {
      setSeleccionado(pedido)   // fallback: sin detalle de ítems
    }
  }

  const cambiarEstado = async (pedidoId, estadoId) => {
    try {
      const res = await fetch(`${API}/admin/pedidos/${pedidoId}/estado/`, {
        method:  'PATCH',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body:    JSON.stringify({ estado_id: estadoId }),
      })
      if (!res.ok) throw new Error()
      const data = await res.json()
      // Actualizar en la lista
      setPedidos(ps => ps.map(p =>
        p.pedido_id === pedidoId
          ? { ...p, estado_id: data.estado_id, estado_nombre: data.estado_nombre }
          : p
      ))
      // Actualizar en el modal y en caché
      if (seleccionado?.pedido_id === pedidoId) {
        const updated = { ...seleccionado, estado_id: data.estado_id, estado_nombre: data.estado_nombre }
        setSeleccionado(updated)
        setDetalleCache(c => ({ ...c, [pedidoId]: updated }))
      }
    } catch { alert('Error al cambiar el estado') }
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2>Pedidos <span className={styles.count}>{total}</span></h2>
        <div className={styles.filtros}>
          <div className={styles.searchBox}>
            <Search size={16} />
            <input
              placeholder="Buscar por cliente o #pedido…"
              value={search}
              onChange={e => { setSearch(e.target.value); setPage(1) }}
            />
          </div>
          <select
            value={filtroEst}
            onChange={e => { setFiltroEst(e.target.value); setPage(1) }}
          >
            <option value="">Todos los estados</option>
            {estados.map(e => <option key={e.estado_id} value={e.estado_id}>{e.nombre}</option>)}
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
                  <th>#</th><th>Cliente</th><th>Ciudad</th>
                  <th>Ítems</th><th>Total</th><th>Fecha</th>
                  <th>Estado</th><th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {pedidos.length === 0 ? (
                  <tr><td colSpan={8} className={styles.empty}>Sin resultados</td></tr>
                ) : pedidos.map(p => (
                  <tr key={p.pedido_id}>
                    <td className={styles.idCell}>#{p.pedido_id}</td>
                    <td>
                      <div className={styles.clienteCell}>
                        <strong>{p.cliente_nombre}</strong>
                        <span>{p.cliente_email}</span>
                      </div>
                    </td>
                    <td>{p.ciudad || '—'}</td>
                    <td className={styles.center}>{p.num_items}</td>
                    <td className={styles.totalCell}>${parseFloat(p.total).toLocaleString('es-CO')}</td>
                    <td>{new Date(p.fecha_pedido).toLocaleDateString('es-CO')}</td>
                    <td>
                      <select
                        className={styles.statusSelect}
                        value={p.estado_id}
                        style={{ '--color': COLOR_ESTADO[p.estado_nombre] ?? '#888' }}
                        onChange={e => cambiarEstado(p.pedido_id, Number(e.target.value))}
                      >
                        {estados.map(e => <option key={e.estado_id} value={e.estado_id}>{e.nombre}</option>)}
                      </select>
                    </td>
                    <td>
                      <button className={styles.btnVer} onClick={() => abrirDetalle(p)}>
                        <Eye size={15} /> Ver
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Paginación */}
          {pages > 1 && (
            <div className={styles.paginacion}>
              <button disabled={page <= 1}    onClick={() => setPage(p => p - 1)}><ChevronLeft  size={16} /></button>
              <span>Página {page} de {pages}</span>
              <button disabled={page >= pages} onClick={() => setPage(p => p + 1)}><ChevronRight size={16} /></button>
            </div>
          )}
        </>
      )}

      {seleccionado && (
        <ModalDetalle
          pedido={seleccionado}
          estados={estados}
          onCerrar={() => setSeleccionado(null)}
          onCambiarEstado={cambiarEstado}
        />
      )}
    </div>
  )
}