import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Package, ChevronDown, ChevronUp, ShoppingBag } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import styles from './MisPedidos.module.css'

// Mock — reemplazar por fetch /api/mis-pedidos cuando el backend esté listo
const MOCK_PEDIDOS = [
  {
    id: 'PED-003',
    fecha: '2026-03-09',
    total: 215000,
    estado: 'Pendiente de preparación',
    items: [
      { producto: 'Panel Japonés', ancho: 180, alto: 240, area: 0.432, precio_m2: 250000, total: 108000 },
    ],
  },
  {
    id: 'PED-001',
    fecha: '2026-03-10',
    total: 320000,
    estado: 'Enviado',
    items: [
      { producto: 'Cortina Blackout',   ancho: 200, alto: 250, area: 0.5,  precio_m2: 160000, total: 80000 },
      { producto: 'Persiana Enrollable',ancho: 150, alto: 160, area: 0.24, precio_m2: 180000, total: 43200 },
    ],
  },
]

const ESTADO_STYLE = {
  'Pendiente de preparación': { color: '#ffc107', bg: 'rgba(255,193,7,0.1)',  border: 'rgba(255,193,7,0.2)'  },
  'Preparado':                { color: '#cfe795', bg: 'rgba(207,231,149,0.1)',border: 'rgba(207,231,149,0.2)' },
  'Enviado':                  { color: '#8fc263', bg: 'rgba(143,194,99,0.1)', border: 'rgba(143,194,99,0.2)'  },
}

// Barra de progreso por estado
const PASOS = ['Pendiente de preparación', 'Preparado', 'Enviado']

function BarraEstado({ estado }) {
  const idx = PASOS.indexOf(estado)
  return (
    <div className={styles.progressBar}>
      {PASOS.map((paso, i) => (
        <div key={paso} className={styles.progressStep}>
          <div className={`${styles.progressDot} ${i <= idx ? styles.progressDotActive : ''}`}>
            {i <= idx && <span className={styles.progressCheck}>✓</span>}
          </div>
          <span className={`${styles.progressLabel} ${i <= idx ? styles.progressLabelActive : ''}`}>
            {paso}
          </span>
          {i < PASOS.length - 1 && (
            <div className={`${styles.progressLine} ${i < idx ? styles.progressLineActive : ''}`} />
          )}
        </div>
      ))}
    </div>
  )
}

function PedidoCard({ pedido }) {
  const [open, setOpen] = useState(false)
  const estilo = ESTADO_STYLE[pedido.estado] || {}

  return (
    <div className={styles.card}>
      {/* Cabecera */}
      <div className={styles.cardHeader} onClick={() => setOpen(v => !v)}>
        <div className={styles.cardHeaderLeft}>
          <Package size={18} className={styles.cardIcon} />
          <div>
            <span className={styles.cardId}>{pedido.id}</span>
            <span className={styles.cardFecha}>{pedido.fecha}</span>
          </div>
        </div>
        <div className={styles.cardHeaderRight}>
          <span
            className={styles.estadoBadge}
            style={{ color: estilo.color, background: estilo.bg, borderColor: estilo.border }}
          >
            {pedido.estado}
          </span>
          <span className={styles.cardTotal}>
            ${pedido.total.toLocaleString('es-CO')}
          </span>
          {open ? <ChevronUp size={16} className={styles.chevron} /> : <ChevronDown size={16} className={styles.chevron} />}
        </div>
      </div>

      {/* Detalle expandible */}
      {open && (
        <div className={styles.cardBody}>
          <BarraEstado estado={pedido.estado} />

          <table className={styles.itemsTable}>
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
              {pedido.items.map((item, i) => (
                <tr key={i}>
                  <td className={styles.tdNombre}>{item.producto}</td>
                  <td className={styles.tdMuted}>{item.ancho} × {item.alto} cm</td>
                  <td>{item.area} m²</td>
                  <td>${item.precio_m2.toLocaleString('es-CO')}</td>
                  <td className={styles.tdGreen}>${item.total.toLocaleString('es-CO')}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className={styles.totalRow}>
            <span className={styles.totalLabel}>Total del pedido</span>
            <span className={styles.totalValue}>${pedido.total.toLocaleString('es-CO')}</span>
          </div>
        </div>
      )}
    </div>
  )
}

export default function MisPedidos() {
  const { user } = useAuth()

  return (
    <div className={styles.page}>
      <div className={styles.inner}>

        <div className={styles.pageHeader}>
          <h1 className={styles.pageTitle}>Mis pedidos</h1>
          <p className={styles.pageSub}>Hola, <strong>{user?.nombre?.split(' ')[0]}</strong> — aquí están todos tus pedidos.</p>
        </div>

        {MOCK_PEDIDOS.length === 0 ? (
          <div className={styles.empty}>
            <ShoppingBag size={52} className={styles.emptyIcon} />
            <h2 className={styles.emptyTitle}>Aún no tienes pedidos</h2>
            <p className={styles.emptySub}>Cuando realices tu primera compra aparecerá aquí.</p>
            <Link to="/tienda" className={styles.btnPrimary}>Ir a la tienda</Link>
          </div>
        ) : (
          <div className={styles.list}>
            {MOCK_PEDIDOS.map(p => <PedidoCard key={p.id} pedido={p} />)}
          </div>
        )}
      </div>
    </div>
  )
}