import { Link } from 'react-router-dom'
import Hero from '../../components/Hero/Hero'
import ProductCard from '../../components/ProductCard/ProductCard'
import styles from './Home.module.css'

// Datos mock — se reemplazan por llamadas a la API
const PRODUCTOS_DESTACADOS = [
  { producto_id: 1, nombre: 'Cortina Clásica', precio_m2: 120000, categoria: 'Cortinas',  imagen_principal: 'https://images.unsplash.com/photo-1586105251261-72a756497a11?w=600&q=75' },
  { producto_id: 2, nombre: 'Persiana Enrollable', precio_m2: 180000, categoria: 'Persianas', imagen_principal: 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600&q=75' },
  { producto_id: 3, nombre: 'Panel Japonés', precio_m2: 250000, categoria: 'Paneles',    imagen_principal: 'https://images.unsplash.com/photo-1585128903994-9788298ef4fd?w=600&q=75' },
]

const CATEGORIAS = [
  { nombre: 'Cortinas',  desc: 'Elegancia y suavidad para cada ambiente', img: 'https://images.unsplash.com/photo-1586105251261-72a756497a11?w=800&q=75' },
  { nombre: 'Persianas', desc: 'Control de luz con diseño moderno',        img: 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800&q=75' },
  { nombre: 'Accesorios', desc: 'El detalle que lo completa todo',         img: 'https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=800&q=75' },
]

export default function Home() {
  return (
    <>
      <Hero />

      {/* ── Sección Categorías ─────────────────────────────────────────── */}
      <section className={styles.section}>
        <div className="container">
          <div className={styles.sectionHeader}>
            <p className={styles.eyebrow}>Colecciones</p>
            <h2 className={styles.sectionTitle}>Encuentra tu estilo</h2>
          </div>
          <div className={styles.categoriasGrid}>
            {CATEGORIAS.map((cat) => (
              <Link
                key={cat.nombre}
                to={`/tienda?categoria=${cat.nombre}`}
                className={styles.categoriaCard}
              >
                <img src={cat.img} alt={cat.nombre} className={styles.categoriaImg} loading="lazy" />
                <div className={styles.categoriaOverlay} />
                <div className={styles.categoriaInfo}>
                  <h3 className={styles.categoriaNombre}>{cat.nombre}</h3>
                  <p className={styles.categoriaDesc}>{cat.desc}</p>
                  <span className={styles.categoriaLink}>Explorar →</span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* ── Sección Productos Destacados ──────────────────────────────── */}
      <section className={styles.section}>
        <div className="container">
          <div className={styles.sectionHeader}>
            <p className={styles.eyebrow}>Destacados</p>
            <h2 className={styles.sectionTitle}>Nuestros Productos</h2>
          </div>
          <div className={styles.productosGrid}>
            {PRODUCTOS_DESTACADOS.map((p) => (
              <ProductCard key={p.producto_id} product={p} />
            ))}
          </div>
          <div className={styles.verTodos}>
            <Link to="/tienda" className={styles.verTodosBtn}>Ver toda la colección</Link>
          </div>
        </div>
      </section>

      {/* ── Sección ¿Por qué nosotros? ────────────────────────────────── */}
      <section className={`${styles.section} ${styles.sectionDark}`}>
        <div className="container">
          <div className={styles.sectionHeader}>
            <p className={styles.eyebrow}>Nuestro proceso</p>
            <h2 className={styles.sectionTitle}>Hecho a tu medida</h2>
          </div>
          <div className={styles.procesosGrid}>
            {[
              { icon: '📐', title: 'Mide tu espacio',       desc: 'Te guiamos con instrucciones claras y video para que tomes las medidas perfectas.' },
              { icon: '🛒', title: 'Elige y personaliza',   desc: 'Selecciona tu producto, ingresa tus medidas y el sistema calcula el precio al instante.' },
              { icon: '💳', title: 'Paga de forma segura',  desc: 'Pasarela de pagos integrada con tarjeta débito, crédito o PSE. Recibe tu factura electrónica.' },
              { icon: '🚚', title: 'Recibe e instala',      desc: 'Fabricamos a tu medida y te lo enviamos. También ofrecemos servicio de instalación.' },
            ].map((paso) => (
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