
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import {
  ShoppingBag, Package, Users, TrendingUp,
  AlertTriangle, CheckCircle, Clock, ArrowRight
} from 'lucide-react'
import {
  XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, AreaChart, Area
} from 'recharts'
import styles from './Dashboard.module.css'

const API = import.meta.env.VITE_API_URL

const METRIC_CONFIG = [
  { key: 'pedidos_mes', icon: ShoppingBag, color: '#8fc263' },
  { key: 'ingresos_mes', icon: TrendingUp, color: '#cfe795' },
  { key: 'productos_activos', icon: Package, color: '#8fc263' },
  { key: 'clientes', icon: Users, color: '#cfe795' },
]

const ESTADO_COLORS = {
  'Enviado':                  { bg: 'rgba(143,194,99,0.12)',  color: '#8fc263'  },
  'Preparado':                { bg: 'rgba(207,231,149,0.12)', color: '#cfe795'  },
  'Pendiente de preparación': { bg: 'rgba(255,193,7,0.12)',   color: '#ffc107'  },
}

const ALERTA_ICONS = {
  warning: <AlertTriangle size={15} color="#ffc107" />,
  info:    <Clock         size={15} color="#8fc263" />,
  success: <CheckCircle   size={15} color="#cfe795" />,
}

export default function AdminDashboard() {
  const { token } = useAuth()
  const [data, setData] = useState({
    periodo_label: '',
    metrics: {},
    ventas_mes: [],
    pedidos_recientes: [],
    top_productos: [],
    alertas: [],
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  const formatCop = useMemo(() => new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    maximumFractionDigits: 0,
  }), [])

  useEffect(() => {
    const cargar = async () => {
      setLoading(true)
      setError(false)
      try {
        const res = await fetch(`${API}/admin/dashboard/`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (!res.ok) throw new Error('Respuesta no OK')
        const payload = await res.json()
        setData({
          periodo_label: payload.periodo_label ?? '',
          metrics: payload.metrics ?? {},
          ventas_mes: payload.ventas_mes ?? [],
          pedidos_recientes: payload.pedidos_recientes ?? [],
          top_productos: payload.top_productos ?? [],
          alertas: payload.alertas ?? [],
        })
      } catch {
        setError(true)
        setData({
          periodo_label: '',
          metrics: {},
          ventas_mes: [],
          pedidos_recientes: [],
          top_productos: [],
          alertas: [],
        })
      } finally {
        setLoading(false)
      }
    }

    if (token) {
      cargar()
    } else {
      setLoading(false)
      setError(true)
    }
  }, [token])

  const fmtY = (v) => v >= 1000000 ? `$${(v / 1000000).toFixed(1)}M` : `$${(v / 1000).toFixed(0)}K`

  const renderMetricValue = (key, value) => {
    if (key === 'ingresos_mes') return formatCop.format(value || 0)
    return value ?? 0
  }

  return (
    <div className={styles.page}>

      {/* Encabezado */}
      <div className={styles.pageHeader}>
        <div>
          <h1 className={styles.pageTitle}>Dashboard</h1>
          <p className={styles.pageSub}>
            Resumen general{data.periodo_label ? ` — ${data.periodo_label}` : ''}
          </p>
        </div>
      </div>

      {error && !loading && (
        <div className={styles.alertas}>
          <div className={`${styles.alerta} ${styles.alerta_warning}`}>
            <AlertTriangle size={15} color="#ffc107" />
            <span>No se pudo cargar el dashboard. Verifica el backend.</span>
          </div>
        </div>
      )}

      {/* Alertas */}
      {data.alertas.length > 0 && (
        <div className={styles.alertas}>
          {data.alertas.map((a, i) => (
            <div key={i} className={`${styles.alerta} ${styles['alerta_' + a.tipo]}`}>
              {ALERTA_ICONS[a.tipo]}
              <span>{a.msg}</span>
            </div>
          ))}
        </div>
      )}

      {/* Metricas */}
      <div className={styles.metricsGrid}>
        {METRIC_CONFIG.map((m) => {
          const metric = data.metrics[m.key] || { label: '', value: 0, delta: '0' }
          return (
            <div key={m.key} className={styles.metricCard}>
              <div className={styles.metricIcon} style={{ color: m.color, background: m.color + '18' }}>
                <m.icon size={20} />
              </div>
              <div className={styles.metricInfo}>
                <span className={styles.metricValue}>{renderMetricValue(m.key, metric.value)}</span>
                <span className={styles.metricLabel}>{metric.label}</span>
              </div>
              <span className={styles.metricDelta} style={{ color: String(metric.delta || '').startsWith('+') ? '#8fc263' : '#888' }}>
                {metric.delta}
              </span>
            </div>
          )
        })}
      </div>

      {/* Grafica + Top productos */}
      <div className={styles.midRow}>

        {/* Grafica ventas */}
        <div className={styles.card} style={{ flex: 2 }}>
          <div className={styles.cardHeader}>
            <h2 className={styles.cardTitle}>Ventas por mes</h2>
            <span className={styles.cardSub}>Ultimos 6 meses</span>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={data.ventas_mes} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="greenGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8fc263" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#8fc263" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="mes" tick={{ fill: '#666', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tickFormatter={fmtY} tick={{ fill: '#666', fontSize: 11 }} axisLine={false} tickLine={false} width={52} />
              <Tooltip
                contentStyle={{ background: '#111', border: '1px solid rgba(143,194,99,0.2)', borderRadius: 7, fontSize: 12 }}
                labelStyle={{ color: '#f7efd3' }}
                formatter={(v) => [formatCop.format(v), 'Ventas']}
              />
              <Area type="monotone" dataKey="ventas" stroke="#8fc263" strokeWidth={2} fill="url(#greenGrad)" dot={{ fill: '#8fc263', r: 3 }} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Top productos */}
        <div className={styles.card} style={{ flex: 1, minWidth: 240 }}>
          <div className={styles.cardHeader}>
            <h2 className={styles.cardTitle}>Top productos</h2>
            <span className={styles.cardSub}>Por unidades</span>
          </div>
          <div className={styles.topList}>
            {data.top_productos.length === 0 ? (
              <div className={styles.empty}>Sin datos</div>
            ) : data.top_productos.map((p, i) => (
              <div key={p.nombre} className={styles.topItem}>
                <span className={styles.topRank}>{i + 1}</span>
                <div className={styles.topInfo}>
                  <span className={styles.topNombre}>{p.nombre}</span>
                  <span className={styles.topIngresos}>{formatCop.format(p.ingresos || 0)}</span>
                </div>
                <span className={styles.topVentas}>{p.ventas} uds</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Pedidos recientes */}
      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <h2 className={styles.cardTitle}>Pedidos recientes</h2>
          <Link to="/admin/pedidos" className={styles.cardLink}>
            Ver todos <ArrowRight size={13} />
          </Link>
        </div>
        <div className={styles.tableWrapper}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>ID</th>
                <th>Cliente</th>
                <th>Total</th>
                <th>Estado</th>
                <th>Fecha</th>
              </tr>
            </thead>
            <tbody>
              {data.pedidos_recientes.length === 0 ? (
                <tr><td colSpan={5} className={styles.empty}>Sin pedidos</td></tr>
              ) : data.pedidos_recientes.map(p => (
                <tr key={p.id}>
                  <td className={styles.tdMono}>{p.id}</td>
                  <td>{p.cliente}</td>
                  <td className={styles.tdGreen}>{formatCop.format(p.total || 0)}</td>
                  <td>
                    <span
                      className={styles.badge}
                      style={ESTADO_COLORS[p.estado]}
                    >
                      {p.estado}
                    </span>
                  </td>
                  <td className={styles.tdMuted}>{new Date(p.fecha).toLocaleDateString('es-CO')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  )
}
