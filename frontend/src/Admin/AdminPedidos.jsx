import { useState } from 'react'
import { Search, X, ChevronDown, Eye } from 'lucide-react'
import styles from './AdminPedidos.module.css'

const ESTADOS = ['Pendiente de preparación', 'Preparado', 'Enviado']
const ESTADO_STYLE = {
  'Pendiente de preparación': { bg: 'rgba(255,193,7,0.1)',  color: '#ffc107', border: 'rgba(255,193,7,0.2)'  },
  'Preparado':                { bg: 'rgba(207,231,149,0.1)',color: '#cfe795', border: 'rgba(207,231,149,0.2)' },
  'Enviado':                  { bg: 'rgba(143,194,99,0.1)', color: '#8fc263', border: 'rgba(143,194,99,0.2)'  },
}

const INITIAL_PEDIDOS = [
  { id: 'PED-001', cliente: 'María Pérez',       email: 'maria.perez@example.com',       total: 320000,  estado: 'Enviado',                 fecha: '2026-03-10', items: [{producto:'Cortina Blackout', ancho:200, alto:250, area:0.5, precio_m2:160000, total:80000, cantidad:1}, {producto:'Persiana Enrollable', ancho:150, alto:160, area:0.24, precio_m2:180000, total:43200, cantidad:1}] },
  { id: 'PED-002', cliente: 'Carlos Rodríguez',  email: 'carlos.rodriguez@example.com',  total: 780000,  estado: 'Preparado',               fecha: '2026-03-10', items: [{producto:'Persiana Zebra',    ancho:300, alto:250, area:0.75, precio_m2:200000, total:150000, cantidad:2}] },
  { id: 'PED-003', cliente: 'Laura Gómez',       email: 'laura.gomez@gmail.com',         total: 215000,  estado: 'Pendiente de preparación',fecha: '2026-03-09', items: [{producto:'Panel Japonés',     ancho:180, alto:240, area:0.432, precio_m2:250000, total:108000, cantidad:1}] },
  { id: 'PED-004', cliente: 'Jorge Martínez',    email: 'jorge.m@example.com',           total: 540000,  estado: 'Enviado',                 fecha: '2026-03-09', items: [{producto:'Cortina Clásica',   ancho:250, alto:280, area:0.7, precio_m2:120000, total:84000, cantidad:2}] },
  { id: 'PED-005', cliente: 'Ana Torres',        email: 'ana.torres@example.com',        total: 190000,  estado: 'Pendiente de preparación',fecha: '2026-03-08', items: [{producto:'Persiana Veneciana',ancho:120, alto:180, area:0.216, precio_m2:140000, total:30240, cantidad:1}] },
  { id: 'PED-006', cliente: 'Luis Herrera',      email: 'luis.h@example.com',            total: 420000,  estado: 'Preparado',               fecha: '2026-03-07', items: [{producto:'Cortina Sheer',     ancho:300, alto:250, area:0.75, precio_m2:95000, total:71250, cantidad:2}] },
]

const fmt = (n) => `$${Number(n).toLocaleString('es-CO')}`

export default function AdminPedidos() {
  const [pedidos, setPedidos] = useState(INITIAL_PEDIDOS)
  const [search, setSearch]   = useState('')
  const [filter, setFilter]   = useState('Todos')
  const [detalle, setDetalle] = useState(null)

  const filtered = pedidos.filter(p => {
    const matchS = p.cliente.toLowerCase().includes(search.toLowerCase()) || p.id.includes(search)
    const matchF = filter === 'Todos' || p.estado === filter
    return matchS && matchF
  })

  const cambiarEstado = (id, nuevoEstado) => {
    setPedidos(prev => prev.map(p => p.id === id ? { ...p, estado: nuevoEstado } : p))
    if (detalle?.id === id) setDetalle(prev => ({ ...prev, estado: nuevoEstado }))
  }

  return (
    <div className={styles.page}>

      <div className={styles.pageHeader}>
        <div>
          <h1 className={styles.pageTitle}>Pedidos</h1>
          <p className={styles.pageSub}>{pedidos.length} pedidos registrados</p>
        </div>
      </div>

      {/* Filtros */}
      <div className={styles.filters}>
        <div className={styles.searchWrapper}>
          <Search size={15} className={styles.searchIcon} />
          <input type="text" placeholder="Buscar por cliente o ID..."
            value={search} onChange={e => setSearch(e.target.value)}
            className={styles.searchInput} />
          {search && <button className={styles.clearSearch} onClick={() => setSearch('')}><X size={14} /></button>}
        </div>
        <div className={styles.pills}>
          {['Todos', ...ESTADOS].map(e => (
            <button key={e}
              className={`${styles.pill} ${filter === e ? styles.pillActive : ''}`}
              onClick={() => setFilter(e)}
            >{e}</button>
          ))}
        </div>
      </div>

      {/* Tabla */}
      <div className={styles.tableCard}>
        <div className={styles.tableWrapper}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>ID</th>
                <th>Cliente</th>
                <th>Total</th>
                <th>Estado</th>
                <th>Fecha</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 && (
                <tr><td colSpan={6} className={styles.empty}>Sin resultados</td></tr>
              )}
              {filtered.map(p => (
                <tr key={p.id}>
                  <td className={styles.tdMono}>{p.id}</td>
                  <td>
                    <div className={styles.clienteCell}>
                      <span className={styles.clienteNombre}>{p.cliente}</span>
                      <span className={styles.clienteEmail}>{p.email}</span>
                    </div>
                  </td>
                  <td className={styles.tdGreen}>{fmt(p.total)}</td>
                  <td>
                    <StatusSelect
                      value={p.estado}
                      onChange={(v) => cambiarEstado(p.id, v)}
                    />
                  </td>
                  <td className={styles.tdMuted}>{p.fecha}</td>
                  <td>
                    <button className={styles.viewBtn} onClick={() => setDetalle(p)}>
                      <Eye size={14} /> Ver
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Modal detalle pedido ──────────────────────────── */}
      {detalle && (
        <div className={styles.overlay} onClick={() => setDetalle(null)}>
          <div className={styles.modal} onClick={e => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <div>
                <h2 className={styles.modalTitle}>{detalle.id}</h2>
                <p className={styles.modalSub}>{detalle.cliente} · {detalle.fecha}</p>
              </div>
              <button className={styles.modalClose} onClick={() => setDetalle(null)}><X size={18} /></button>
            </div>
            <div className={styles.modalBody}>
              {/* Estado editable dentro del modal también */}
              <div className={styles.modalEstado}>
                <span className={styles.modalEstadoLabel}>Estado actual:</span>
                <StatusSelect
                  value={detalle.estado}
                  onChange={(v) => cambiarEstado(detalle.id, v)}
                />
              </div>
              <div className={styles.modalDivider} />
              <h3 className={styles.modalSection}>Ítems del pedido</h3>
              <table className={styles.detalleTable}>
                <thead>
                  <tr>
                    <th>Producto</th>
                    <th>Medidas</th>
                    <th>Área m²</th>
                    <th>Precio/m²</th>
                    <th>Total</th>
                  </tr>
                </thead>
                <tbody>
                  {detalle.items.map((item, i) => (
                    <tr key={i}>
                      <td>{item.producto}</td>
                      <td className={styles.tdMuted}>{item.ancho} × {item.alto} cm</td>
                      <td>{item.area} m²</td>
                      <td>{fmt(item.precio_m2)}</td>
                      <td className={styles.tdGreen}>{fmt(item.total)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className={styles.totalRow}>
                <span className={styles.totalLabel}>Total del pedido</span>
                <span className={styles.totalValue}>{fmt(detalle.total)}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// Select de estado con color dinámico
function StatusSelect({ value, onChange }) {
  const style = ESTADO_STYLE[value] || {}
  return (
    <div className={styles.statusSelect} style={{ background: style.bg, borderColor: style.border }}>
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        style={{ color: style.color }}
        className={styles.statusSelectInput}
      >
        {ESTADOS.map(e => <option key={e} value={e}>{e}</option>)}
      </select>
      <ChevronDown size={12} style={{ color: style.color, flexShrink: 0, pointerEvents: 'none' }} />
    </div>
  )
}