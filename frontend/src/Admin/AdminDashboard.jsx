import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ShoppingBag, Package, Users, TrendingUp,
  AlertTriangle, CheckCircle, Clock, ArrowRight
} from 'lucide-react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, AreaChart, Area
} from 'recharts'
import styles from './Dashboard.module.css'

// ── Mock data (reemplazar por fetch /api/admin/dashboard) ─
const METRICS = [
  { label: 'Pedidos este mes',  value: 38,          delta: '+12%', icon: ShoppingBag, color: '#8fc263' },
  { label: 'Ingresos (COP)',    value: '$4.280.000', delta: '+8%',  icon: TrendingUp,  color: '#cfe795' },
  { label: 'Productos activos', value: 10,           delta: '0',    icon: Package,     color: '#8fc263' },
  { label: 'Clientes',          value: 24,           delta: '+3',   icon: Users,       color: '#cfe795' },
]

const VENTAS_MES = [
  { mes: 'Oct', ventas: 1200000 },
  { mes: 'Nov', ventas: 1950000 },
  { mes: 'Dic', ventas: 3100000 },
  { mes: 'Ene', ventas: 2400000 },
  { mes: 'Feb', ventas: 3600000 },
  { mes: 'Mar', ventas: 4280000 },
]

const PEDIDOS_RECIENTES = [
  { id: 'PED-001', cliente: 'María Pérez',      total: '$320.000',  estado: 'Enviado',                 fecha: '10 mar' },
  { id: 'PED-002', cliente: 'Carlos Rodríguez', total: '$780.000',  estado: 'Preparado',               fecha: '10 mar' },
  { id: 'PED-003', cliente: 'Laura Gómez',      total: '$215.000',  estado: 'Pendiente de preparación',fecha: '09 mar' },
  { id: 'PED-004', cliente: 'Jorge Martínez',   total: '$540.000',  estado: 'Enviado',                 fecha: '09 mar' },
  { id: 'PED-005', cliente: 'Ana Torres',        total: '$190.000',  estado: 'Pendiente de preparación',fecha: '08 mar' },
]

const TOP_PRODUCTOS = [
  { nombre: 'Persiana Zebra',     ventas: 14, ingresos: '$2.800.000' },
  { nombre: 'Cortina Blackout',   ventas: 11, ingresos: '$1.760.000' },
  { nombre: 'Persiana Enrollable',ventas:  8, ingresos: '$1.440.000' },
  { nombre: 'Panel Japonés',      ventas:  5, ingresos: '$1.250.000' },
]

const ALERTAS = [
  { tipo: 'warning', msg: '3 pedidos llevan más de 48h en "Pendiente de preparación"' },
  { tipo: 'info',    msg: 'El producto "Riel de Aluminio Doble" no tiene imagen principal' },
  { tipo: 'success', msg: '5 pedidos completados esta semana sin incidencias' },
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

// Formatea eje Y en millones
const fmtY = (v) => v >= 1000000 ? `$${(v/1000000).toFixed(1)}M` : `$${(v/1000).toFixed(0)}K`

export default function AdminDashboard() {
  return (
    <div className={styles.page}>

      {/* ── Encabezado ──────────────────────────────────── */}
      <div className={styles.pageHeader}>
        <div>
          <h1 className={styles.pageTitle}>Dashboard</h1>
          <p className={styles.pageSub}>Resumen general — Marzo 2026</p>
        </div>
      </div>

      {/* ── Alertas ─────────────────────────────────────── */}
      <div className={styles.alertas}>
        {ALERTAS.map((a, i) => (
          <div key={i} className={`${styles.alerta} ${styles['alerta_' + a.tipo]}`}>
            {ALERTA_ICONS[a.tipo]}
            <span>{a.msg}</span>
          </div>
        ))}
      </div>

      {/* ── Métricas ────────────────────────────────────── */}
      <div className={styles.metricsGrid}>
        {METRICS.map((m) => (
          <div key={m.label} className={styles.metricCard}>
            <div className={styles.metricIcon} style={{ color: m.color, background: m.color + '18' }}>
              <m.icon size={20} />
            </div>
            <div className={styles.metricInfo}>
              <span className={styles.metricValue}>{m.value}</span>
              <span className={styles.metricLabel}>{m.label}</span>
            </div>
            <span className={styles.metricDelta} style={{ color: m.delta.startsWith('+') ? '#8fc263' : '#888' }}>
              {m.delta}
            </span>
          </div>
        ))}
      </div>

      {/* ── Gráfica + Top productos ──────────────────────── */}
      <div className={styles.midRow}>

        {/* Gráfica ventas */}
        <div className={styles.card} style={{ flex: 2 }}>
          <div className={styles.cardHeader}>
            <h2 className={styles.cardTitle}>Ventas por mes</h2>
            <span className={styles.cardSub}>Últimos 6 meses</span>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={VENTAS_MES} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="greenGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#8fc263" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#8fc263" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="mes" tick={{ fill: '#666', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tickFormatter={fmtY} tick={{ fill: '#666', fontSize: 11 }} axisLine={false} tickLine={false} width={52} />
              <Tooltip
                contentStyle={{ background: '#111', border: '1px solid rgba(143,194,99,0.2)', borderRadius: 7, fontSize: 12 }}
                labelStyle={{ color: '#f7efd3' }}
                formatter={(v) => [`$${v.toLocaleString('es-CO')}`, 'Ventas']}
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
            {TOP_PRODUCTOS.map((p, i) => (
              <div key={p.nombre} className={styles.topItem}>
                <span className={styles.topRank}>{i + 1}</span>
                <div className={styles.topInfo}>
                  <span className={styles.topNombre}>{p.nombre}</span>
                  <span className={styles.topIngresos}>{p.ingresos}</span>
                </div>
                <span className={styles.topVentas}>{p.ventas} uds</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Pedidos recientes ───────────────────────────── */}
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
              {PEDIDOS_RECIENTES.map(p => (
                <tr key={p.id}>
                  <td className={styles.tdMono}>{p.id}</td>
                  <td>{p.cliente}</td>
                  <td className={styles.tdGreen}>{p.total}</td>
                  <td>
                    <span
                      className={styles.badge}
                      style={ESTADO_COLORS[p.estado]}
                    >
                      {p.estado}
                    </span>
                  </td>
                  <td className={styles.tdMuted}>{p.fecha}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  )
}