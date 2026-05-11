import { Link } from 'react-router-dom'
import styles from './ProductCard.module.css'

const formatCOP = (n) =>
  new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(n)

export default function ProductCard({ product }) {
  const {
    producto_id,
    nombre,
    precio_m2,
    categoria,          // puede venir como nombre (mock) o como ID (backend)
    categoria_nombre,   // el backend lo envía así desde ProductoListSerializer
    imagen_principal,   // URL directa — campo calculado del serializer
  } = product

  // Categoria a mostrar: preferir categoria_nombre del backend
  const catLabel = categoria_nombre || categoria || ''

  // Imagen: el backend devuelve imagen_principal como string URL o null
  const imgSrc = imagen_principal ||
    'https://images.unsplash.com/photo-1585128903994-9788298ef4fd?w=600&q=75'

  return (
    <Link to={`/producto/${producto_id}`} className={styles.card}>
      <div className={styles.imageWrapper}>
        <img
          src={imgSrc}
          alt={nombre}
          className={styles.image}
          loading="lazy"
          onError={e => {
            // Si la imagen falla, mostrar placeholder
            e.target.src = 'https://images.unsplash.com/photo-1585128903994-9788298ef4fd?w=600&q=75'
          }}
        />
        <div className={styles.overlay} />
        <span className={styles.categoria}>{catLabel}</span>
        <span className={styles.viewMore}>Ver producto →</span>
      </div>
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