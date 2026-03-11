import { Link } from 'react-router-dom'
import styles from './ProductCard.module.css'

// ─── Helpers ──────────────────────────────────────────────────────────────────
const formatCOP = (n) =>
  new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(n)

// ─── Componente ───────────────────────────────────────────────────────────────
export default function ProductCard({ product }) {
  const { producto_id, nombre, precio_m2, categoria, imagen_principal } = product

  return (
    <Link to={`/producto/${producto_id}`} className={styles.card}>
      {/* Imagen */}
      <div className={styles.imageWrapper}>
        <img
          src={imagen_principal || 'https://images.unsplash.com/photo-1585128903994-9788298ef4fd?w=600&q=75'}
          alt={nombre}
          className={styles.image}
          loading="lazy"
        />
        <div className={styles.overlay} />
        <span className={styles.categoria}>{categoria}</span>
        <span className={styles.viewMore}>Ver producto →</span>
      </div>

      {/* Info */}
      <div className={styles.info}>
        <h3 className={styles.nombre}>{nombre}</h3>
        <p className={styles.precio}>
          <span className={styles.precioLabel}>desde </span>
          {formatCOP(precio_m2)}
          <span className={styles.precioUnit}>/m²</span>
        </p>
      </div>
    </Link>
  )
}