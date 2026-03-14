import { useState, useMemo } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ChevronLeft, ShoppingCart, Play, AlertCircle } from 'lucide-react'
import { useCart } from '../../context/CartContext'
import styles from './Detalle.module.css'

// Mock — reemplazar por fetch a la API
const PRODUCTOS = {
  1: {
    producto_id: 1,
    nombre: 'Cortina Clásica',
    descripcion: 'Cortina de tela de alta calidad con caída elegante. Disponible en múltiples telas y colores para adaptarse perfectamente a tu espacio. Fabricación artesanal con acabados de lujo.',
    precio_m2: 120000,
    categoria: 'Cortinas',
    imagenes: [
      'https://images.unsplash.com/photo-1586105251261-72a756497a11?w=800&q=80',
      'https://images.unsplash.com/photo-1567225557594-88887a55d299?w=800&q=80',
      'https://images.unsplash.com/photo-1615874959474-d609969a20ed?w=800&q=80',
    ],
    guia: {
      instrucciones: 'Para cortinas, mide el ancho del riel o barra donde se instalará la cortina. Para el alto, mide desde la parte superior del riel hasta donde deseas que llegue la cortina (suelo, repisa o punto intermedio). Se recomienda agregar al menos 20 cm al ancho para el efecto de vuelo y 5 cm al alto para el dobladillo.',
      video_url: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    },
  },
  2: {
    producto_id: 2,
    nombre: 'Persiana Enrollable',
    descripcion: 'Persiana enrollable de tela técnica con mecanismo de cadena de alta durabilidad. Perfecta para controlar la entrada de luz y dar privacidad a tu espacio.',
    precio_m2: 180000,
    categoria: 'Persianas',
    imagenes: [
      'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800&q=80',
      'https://images.unsplash.com/photo-1449247709967-d4461a6a6103?w=800&q=80',
    ],
    guia: {
      instrucciones: 'Para persianas enrollables, mide el ancho interno del vano (de pared a pared) y el alto desde el techo hasta el suelo. El sistema se instalará dentro del vano. Se recomienda descontar 1 cm del ancho para asegurar un ajuste perfecto.',
      video_url: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    },
  },
}

const formatCOP = (n) =>
  new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(n)

export default function Detalle() {
  const { id } = useParams()
  const { addItem, toggleCart } = useCart()

  const product = PRODUCTOS[id]

  const [imgActiva, setImgActiva]   = useState(0)
  const [ancho,     setAncho]       = useState('')
  const [alto,      setAlto]        = useState('')
  const [errors,    setErrors]      = useState({})
  const [added,     setAdded]       = useState(false)
  const [showVideo, setShowVideo]   = useState(false)

  // Cálculo en tiempo real
  const calculo = useMemo(() => {
    const a = parseFloat(ancho)
    const h = parseFloat(alto)
    if (!a || !h || a <= 0 || h <= 0) return null
    const area = (a * h) / 10000
    const precio = area * product?.precio_m2
    return { area: area.toFixed(4), precio: precio.toFixed(0) }
  }, [ancho, alto, product])

  if (!product) {
    return (
      <div className={styles.notFound}>
        <p>Producto no encontrado.</p>
        <Link to="/tienda" className={styles.backLink}>← Volver a la tienda</Link>
      </div>
    )
  }

  const validate = () => {
    const errs = {}
    if (!ancho || parseFloat(ancho) <= 0) errs.ancho = 'Ingresa el ancho del vano'
    if (!alto  || parseFloat(alto)  <= 0) errs.alto  = 'Ingresa el alto del vano'
    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  const handleAddToCart = () => {
    if (!validate()) return
    addItem(product, parseFloat(ancho), parseFloat(alto))
    setAdded(true)
    setTimeout(() => setAdded(false), 2500)
    toggleCart()
  }

  return (
    <div className={styles.page}>
      <div className="container">
        {/* Breadcrumb */}
        <nav className={styles.breadcrumb}>
          <Link to="/tienda" className={styles.breadBack}>
            <ChevronLeft size={16} /> Tienda
          </Link>
          <span className={styles.breadSep}>/</span>
          <span>{product.categoria}</span>
          <span className={styles.breadSep}>/</span>
          <span className={styles.breadCurrent}>{product.nombre}</span>
        </nav>

        <div className={styles.layout}>
          {/* ── Galería ─────────────────────────────────────────────── */}
          <div className={styles.gallery}>
            <div className={styles.mainImg}>
              <img src={product.imagenes[imgActiva]} alt={product.nombre} />
            </div>
            {product.imagenes.length > 1 && (
              <div className={styles.thumbs}>
                {product.imagenes.map((img, i) => (
                  <button
                    key={i}
                    className={`${styles.thumb} ${imgActiva === i ? styles.thumbActive : ''}`}
                    onClick={() => setImgActiva(i)}
                  >
                    <img src={img} alt={`Vista ${i + 1}`} />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* ── Info + Medidas ──────────────────────────────────────── */}
          <div className={styles.info}>
            <span className={styles.categoria}>{product.categoria}</span>
            <h1 className={styles.nombre}>{product.nombre}</h1>
            <p className={styles.precioBase}>
              <span className={styles.precioLabel}>Precio base: </span>
              {formatCOP(product.precio_m2)}<span className={styles.precioUnit}>/m²</span>
            </p>
            <p className={styles.descripcion}>{product.descripcion}</p>

            <div className={styles.divider} />

            {/* Guía de medidas */}
            <div className={styles.guia}>
              <h3 className={styles.guiaTitulo}>
                <AlertCircle size={16} />
                ¿Cómo tomar las medidas?
              </h3>
              <p className={styles.guiaTexto}>{product.guia.instrucciones}</p>
              {product.guia.video_url && (
                <button
                  className={styles.videoBtn}
                  onClick={() => setShowVideo(v => !v)}
                >
                  <Play size={14} />
                  {showVideo ? 'Ocultar video' : 'Ver video instructivo'}
                </button>
              )}
              {showVideo && (
                <div className={styles.videoWrapper}>
                  <iframe
                    src={product.guia.video_url}
                    title="Video instructivo de medidas"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                    className={styles.video}
                  />
                </div>
              )}
            </div>

            <div className={styles.divider} />

            {/* Formulario de medidas */}
            <div className={styles.medidas}>
              <h3 className={styles.medidasTitulo}>Ingresa tus medidas</h3>
              <div className={styles.medidasGrid}>
                <div className={styles.field}>
                  <label className={styles.label}>Ancho (cm)</label>
                  <input
                    type="number"
                    min="1"
                    placeholder="ej: 150"
                    value={ancho}
                    onChange={e => { setAncho(e.target.value); setErrors(prev => ({ ...prev, ancho: '' })) }}
                    className={`${styles.input} ${errors.ancho ? styles.inputError : ''}`}
                  />
                  {errors.ancho && <span className={styles.errorMsg}>{errors.ancho}</span>}
                </div>
                <div className={styles.field}>
                  <label className={styles.label}>Alto (cm)</label>
                  <input
                    type="number"
                    min="1"
                    placeholder="ej: 220"
                    value={alto}
                    onChange={e => { setAlto(e.target.value); setErrors(prev => ({ ...prev, alto: '' })) }}
                    className={`${styles.input} ${errors.alto ? styles.inputError : ''}`}
                  />
                  {errors.alto && <span className={styles.errorMsg}>{errors.alto}</span>}
                </div>
              </div>

              {/* Resumen de cálculo */}
              {calculo && (
                <div className={styles.calculo}>
                  <div className={styles.calculoRow}>
                    <span>Área calculada</span>
                    <span>{calculo.area} m²</span>
                  </div>
                  <div className={styles.calculoRow}>
                    <span>Precio por m²</span>
                    <span>{formatCOP(product.precio_m2)}</span>
                  </div>
                  <div className={`${styles.calculoRow} ${styles.calculoTotal}`}>
                    <span>Total estimado</span>
                    <span>{formatCOP(parseInt(calculo.precio))}</span>
                  </div>
                  <p className={styles.calculoNota}>* Precio calculado según las medidas ingresadas</p>
                </div>
              )}

              <button
                className={`${styles.addBtn} ${added ? styles.addBtnSuccess : ''}`}
                onClick={handleAddToCart}
              >
                <ShoppingCart size={18} />
                {added ? '¡Agregado al carrito!' : 'Agregar al carrito'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}