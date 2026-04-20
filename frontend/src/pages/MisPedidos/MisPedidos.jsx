import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { Package, ChevronDown, ChevronUp, ShoppingBag, MapPin } from 'lucide-react'
import styles from './MisPedidos.module.css'

// Fallback para desarrollo local si VITE_API_URL no está definida en .env
const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1'

// Mapa de estados del pedido: nombre → { step, color }
// Los nombres deben coincidir exactamente con EstadoPedido.nombre en el backend
const ESTADOS = {
  'Pendiente de preparación': { step: 1, color: '#f59e0b' },
  'Preparado':                { step: 2, color: '#3b82f6' },
  'Enviado':                  { step: 3, color: '#8fc263' },
}

const PASOS_LABEL = [
  'Pendiente de preparación',
  'Preparado',
  'Enviado',
]

/* ── Barra de progreso ────────────────────────────────────── */
function BarraProgreso({ estadoNombre }) {
  const paso = ESTADOS[estadoNombre]?.step ?? 1

  return (
    <div className={styles.progreso}>
      {PASOS_LABEL.map((p, i) => (
        <div key={p} className={styles.pasoWrap}>
          <div className={`${styles.circulo} ${i < paso ? styles.activo : ''}`}>
            {i < paso ? '✓' : i + 1}
          </div>
          <span className={`${styles.pasoLabel} ${i < paso ? styles.activoLabel : ''}`}>
            {p}
          </span>
          {i < PASOS_LABEL.length - 1 && (
            <div className={`${styles.linea} ${i + 1 < paso ? styles.lineaActiva : ''}`} />
          )}
        </div>
      ))}
    </div>
  )
}

/* ── Tarjeta de un pedido ─────────────────────────────────── */
function TarjetaPedido({ pedido }) {
  const [abierto, setAbierto] = useState(false)

  const fecha = new Date(pedido.fecha_pedido).toLocaleDateString('es-CO', {
    year: 'numeric', month: 'long', day: 'numeric',
  })

  return (
    <div className={styles.tarjeta}>
      {/* Encabezado clickeable */}
      <button className={styles.encabezado} onClick={() => setAbierto(a => !a)}>
        <div className={styles.encabezadoLeft}>
          <Package size={18} />
          <span className={styles.pedidoId}>Pedido #{pedido.pedido_id}</span>
          <span className={styles.fecha}>{fecha}</span>
        </div>
        <div className={styles.encabezadoRight}>
          <span className={styles.total}>
            ${parseFloat(pedido.total).toLocaleString('es-CO')}
          </span>
          <span
            className={styles.badge}
            style={{ background: ESTADOS[pedido.estado_nombre]?.color ?? '#666' }}
          >
            {pedido.estado_nombre}
          </span>
          {abierto ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </div>
      </button>

      {/* Detalle colapsable */}
      {abierto && (
        <div className={styles.detalle}>
          <BarraProgreso estadoNombre={pedido.estado_nombre} />

          {pedido.ciudad && (
            <p className={styles.ciudad}>
              <MapPin size={14} /> Entrega en: {pedido.ciudad}
            </p>
          )}

          {/* Tabla de ítems — viene de PedidoDetalleSerializer */}
          {(pedido.detalles || []).length > 0 ? (
            <table className={styles.tabla}>
              <thead>
                <tr>
                  <th>Producto</th>
                  <th>Medidas</th>
                  <th>Área</th>
                  <th>$/m²</th>
                  <th>Cant.</th>
                  <th>Total</th>
                </tr>
              </thead>
              <tbody>
                {pedido.detalles.map(d => (
                  <tr key={d.detalle_id}>
                    <td>
                      <div className={styles.productoCell}>
                        {d.imagen_principal && (
                          <img
                            src={d.imagen_principal}
                            alt={d.nombre}
                            className={styles.thumb}
                            onError={e => { e.target.style.display = 'none' }}
                          />
                        )}
                        <span>{d.nombre}</span>
                      </div>
                    </td>
                    <td>{d.ancho_cm} × {d.alto_cm} cm</td>
                    <td>{parseFloat(d.area_m2).toFixed(2)} m²</td>
                    <td>${parseFloat(d.precio_m2).toLocaleString('es-CO')}</td>
                    <td>{d.cantidad}</td>
                    <td className={styles.tdTotal}>
                      ${parseFloat(d.precio_total).toLocaleString('es-CO')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p style={{ color: '#888', fontSize: '0.85rem' }}>
              Sin ítems registrados.
            </p>
          )}

          <div className={styles.resumen}>
            <span>Total del pedido</span>
            <strong>${parseFloat(pedido.total).toLocaleString('es-CO')}</strong>
          </div>
        </div>
      )}
    </div>
  )
}

/* ── Página principal ─────────────────────────────────────── */
export default function MisPedidos() {
  const { token } = useAuth()
  const [pedidos, setPedidos] = useState([])
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)

  useEffect(() => {
    const cargar = async () => {
      try {
        setLoading(true)
        setError(null)

        const res = await fetch(`${API}/pedidos/`, {
          headers: { Authorization: `Bearer ${token}` },
        })

        if (!res.ok) {
          throw new Error(`Error ${res.status}: no se pudieron cargar los pedidos.`)
        }

        const data = await res.json()
        // El backend devuelve { pedidos: [...], total: N }
        setPedidos(data.pedidos ?? [])
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    if (token) {
      cargar()
    }
  }, [token])

  /* ── Estados de la UI ── */
  if (loading) {
    return (
      <div className={styles.centered} style={{ paddingTop: '80px' }}>
        <div className={styles.spinner} />
        <p>Cargando tus pedidos…</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className={styles.centered} style={{ paddingTop: '80px' }}>
        <p className={styles.errorMsg}>{error}</p>
        <Link to="/tienda" className={styles.btnTienda} style={{ marginTop: '1rem' }}>
          Ir a la tienda
        </Link>
      </div>
    )
  }

  if (pedidos.length === 0) {
    return (
      <div className={styles.vacio} style={{ paddingTop: '80px' }}>
        <ShoppingBag size={64} strokeWidth={1} />
        <h2>Aún no tienes pedidos</h2>
        <p>Cuando realices una compra, aparecerá aquí el historial.</p>
        <Link to="/tienda" className={styles.btnTienda}>
          Ver catálogo
        </Link>
      </div>
    )
  }

  return (
    <main className={styles.container} style={{ paddingTop: 'calc(64px + 2rem)' }}>
      <h1 className={styles.titulo}>Mis Pedidos</h1>
      <p className={styles.subtitulo}>
        {pedidos.length} pedido{pedidos.length !== 1 ? 's' : ''} realizados
      </p>
      <div className={styles.lista}>
        {pedidos.map(p => (
          <TarjetaPedido key={p.pedido_id} pedido={p} />
        ))}
      </div>
    </main>
  )
}