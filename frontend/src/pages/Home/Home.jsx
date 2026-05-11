import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import Hero from '../../components/Hero/Hero'
import ProductCard from '../../components/ProductCard/ProductCard'
import styles from './Home.module.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1'

// Imágenes por defecto para las cards de categorías
const CAT_IMGS = {
  'Cortinas':   'https://images.unsplash.com/photo-1586105251261-72a756497a11?w=800&q=75',
  'Persianas':  'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800&q=75',
  'Accesorios': 'https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=800&q=75',
}
const CAT_DESCS = {
  'Cortinas':   'Elegancia y suavidad para cada ambiente',
  'Persianas':  'Control de luz con diseño moderno',
  'Accesorios': 'El detalle que lo completa todo',
}
const DEFAULT_IMG  = 'https://images.unsplash.com/photo-1586105251261-72a756497a11?w=800&q=75'
const DEFAULT_DESC = 'Descubre nuestra selección de productos'

export default function Home() {
  const [productos,  setProductos]  = useState([])
  const [categorias, setCategorias] = useState([])

  useEffect(() => {
    // Cargar productos destacados (primeros 3 activos)
    fetch(`${API_URL}/catalogo/productos/?page_size=3`)
      .then(r => r.json())
      .then(data => setProductos(Array.isArray(data) ? data : data.results || []))
      .catch(() => {})

    // Cargar categorías activas
    fetch(`${API_URL}/catalogo/categorias/`)
      .then(r => r.json())
      .then(data => setCategorias(Array.isArray(data) ? data : data.results || []))
      .catch(() => {})
  }, [])

  return (
    <>
      <Hero />

      {/* ── Categorías ────────────────────────────────────────── */}
      {categorias.length > 0 && (
        <section className={styles.section}>
          <div className="container">
            <div className={styles.sectionHeader}>
              <p className={styles.eyebrow}>Colecciones</p>
              <h2 className={styles.sectionTitle}>Encuentra tu estilo</h2>
            </div>
            <div className={styles.categoriasGrid}>
              {categorias.slice(0, 3).map(cat => (
                <Link
                  key={cat.categoria_id}
                  to={`/tienda?categoria=${cat.nombre}`}
                  className={styles.categoriaCard}
                >
                  <img
                    src={CAT_IMGS[cat.nombre] || DEFAULT_IMG}
                    alt={cat.nombre}
                    className={styles.categoriaImg}
                    loading="lazy"
                  />
                  <div className={styles.categoriaOverlay} />
                  <div className={styles.categoriaInfo}>
                    <h3 className={styles.categoriaNombre}>{cat.nombre}</h3>
                    <p className={styles.categoriaDesc}>
                      {cat.descripcion || CAT_DESCS[cat.nombre] || DEFAULT_DESC}
                    </p>
                    <span className={styles.categoriaLink}>Explorar →</span>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ── Productos destacados ─────────────────────────────── */}
      {productos.length > 0 && (
        <section className={styles.section}>
          <div className="container">
            <div className={styles.sectionHeader}>
              <p className={styles.eyebrow}>Destacados</p>
              <h2 className={styles.sectionTitle}>Nuestros Productos</h2>
            </div>
            <div className={styles.productosGrid}>
              {productos.map(p => (
                <ProductCard key={p.producto_id} product={p} />
              ))}
            </div>
            <div className={styles.verTodos}>
              <Link to="/tienda" className={styles.verTodosBtn}>Ver toda la colección</Link>
            </div>
          </div>
        </section>
      )}

      {/* ── Proceso ─────────────────────────────────────────── */}
      <section className={`${styles.section} ${styles.sectionDark}`}>
        <div className="container">
          <div className={styles.sectionHeader}>
            <p className={styles.eyebrow}>Nuestro proceso</p>
            <h2 className={styles.sectionTitle}>Hecho a tu medida</h2>
          </div>
          <div className={styles.procesosGrid}>
            {[
              { icon: '📐', title: 'Mide tu espacio',      desc: 'Te guiamos con instrucciones claras para que tomes las medidas perfectas.' },
              { icon: '🛒', title: 'Elige y personaliza',  desc: 'Selecciona tu producto, ingresa tus medidas y el sistema calcula el precio al instante.' },
              { icon: '💳', title: 'Paga de forma segura', desc: 'Pasarela de pagos integrada con tarjeta débito, crédito o PSE.' },
              { icon: '🚚', title: 'Recibe e instala',     desc: 'Fabricamos a tu medida y te lo enviamos. También ofrecemos servicio de instalación.' },
            ].map(paso => (
              <div key={paso.title} className={styles.pasoCard}>
                <span className={styles.pasoIcon}>{paso.icon}</span>
                <h4 className={styles.pasoTitle}>{paso.title}</h4>
                <p className={styles.pasoDesc}>{paso.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
  )
}