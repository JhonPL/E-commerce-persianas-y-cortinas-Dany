import { useState, useMemo, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ChevronLeft, ShoppingCart, AlertCircle, Loader, ImageOff } from 'lucide-react'
import { useCart } from '../../context/CartContext'
import styles from './Detalle.module.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1'

const formatCOP = (n) =>
  new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(n)

// Instrucciones genéricas de medición por categoría
const GUIA_DEFAULT = {
  'Cortinas':   'Mide el ancho del riel o barra y el alto desde la parte superior del riel hasta donde deseas que llegue la cortina. Agrega al menos 20 cm al ancho para el efecto de vuelo.',
  'Persianas':  'Mide el ancho interno del vano (de pared a pared) y el alto desde el techo hasta el suelo. Descuenta 1 cm del ancho para un ajuste perfecto.',
  'Paneles':    'Mide el ancho total del vano y el alto desde el techo hasta el suelo. Cada panel ocupa aproximadamente 60 cm de ancho.',
  'Accesorios': 'Consulta las medidas específicas del accesorio en la descripción del producto.',
}
const GUIA_FALLBACK = 'Mide el ancho y el alto del vano donde se instalará el producto. Ingresa las medidas en centímetros para calcular el precio total.'

export default function Detalle() {
  const { id }               = useParams()
  const { addItem, toggleCart } = useCart()

  const [product,    setProduct]    = useState(null)
  const [loading,    setLoading]    = useState(true)
  const [error,      setError]      = useState('')
  const [imgActiva,  setImgActiva]  = useState(0)
  const [ancho,      setAncho]      = useState('')
  const [alto,       setAlto]       = useState('')
  const [medErrors,  setMedErrors]  = useState({})
  const [added,      setAdded]      = useState(false)

  // Cargar producto del backend
  useEffect(() => {
    setLoading(true); setError(''); setImgActiva(0)
    fetch(`${API_URL}/catalogo/productos/${id}/`)
      .then(r => {
        if (!r.ok) throw new Error('Producto no encontrado')
        return r.json()
      })
      .then(data => setProduct(data))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [id])

  // Cálculo en tiempo real
  const calculo = useMemo(() => {
    if (!product) return null
    const a = parseFloat(ancho)
    const h = parseFloat(alto)
    if (!a || !h || a <= 0 || h <= 0) return null
    const area   = (a * h) / 10000
    const precio = area * product.precio_m2
    return { area: area.toFixed(4), precio: precio.toFixed(0) }
  }, [ancho, alto, product])

  const validate = () => {
    const e = {}
    if (!ancho || parseFloat(ancho) <= 0) e.ancho = 'Ingresa el ancho del vano'
    if (!alto  || parseFloat(alto)  <= 0) e.alto  = 'Ingresa el alto del vano'
    setMedErrors(e)
    return !Object.keys(e).length
  }

  const handleAddToCart = () => {
    if (!validate()) return
    addItem(product, parseFloat(ancho), parseFloat(alto))
    setAdded(true)
    setTimeout(() => setAdded(false), 2500)
    toggleCart()
  }

  /* ── Estados de carga / error ── */
  if (loading) return (
    <div className={styles.centerState}>
      <Loader size={32} className={styles.spinIcon} />
      <p>Cargando producto...</p>
    </div>
  )

  if (error || !product) return (
    <div className={styles.notFound}>
      <p>{error || 'Producto no encontrado.'}</p>
      <Link to="/tienda" className={styles.backLink}>← Volver a la tienda</Link>
    </div>
  )

  // Normalizar imágenes — el backend devuelve [{ imagen_id, url, es_principal, orden }]
  const imagenes = product.imagenes?.length > 0
    ? product.imagenes.map(i => i.url)
    : []

  const categorNombre = product.categoria_nombre || ''
  const guiaTexto     = GUIA_DEFAULT[categorNombre] || GUIA_FALLBACK

  return (
    <div className={styles.page}>
      <div className="container">

        {/* Breadcrumb */}
        <nav className={styles.breadcrumb}>
          <Link to="/tienda" className={styles.breadBack}>
            <ChevronLeft size={16} /> Tienda
          </Link>
          <span className={styles.breadSep}>/</span>
          <span>{categorNombre}</span>
          <span className={styles.breadSep}>/</span>
          <span className={styles.breadCurrent}>{product.nombre}</span>
        </nav>

        <div className={styles.layout}>

          {/* ── Galería ── */}
          <div className={styles.gallery}>
            <div className={styles.mainImg}>
              {imagenes.length > 0
                ? <img src={imagenes[imgActiva]} alt={product.nombre} />
                : (
                  <div className={styles.noImgPlaceholder}>
                    <ImageOff size={48} />
                    <span>Sin imágenes</span>
                  </div>
                )
              }
            </div>
            {imagenes.length > 1 && (
              <div className={styles.thumbs}>
                {imagenes.map((img, i) => (
                  <button key={i}
                    className={`${styles.thumb} ${imgActiva === i ? styles.thumbActive : ''}`}
                    onClick={() => setImgActiva(i)}>
                    <img src={img} alt={`Vista ${i + 1}`} />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* ── Info + medidas ── */}
          <div className={styles.info}>
            <span className={styles.categoria}>{categorNombre}</span>
            <h1 className={styles.nombre}>{product.nombre}</h1>
            <p className={styles.precioBase}>
              <span className={styles.precioLabel}>Precio base: </span>
              {formatCOP(product.precio_m2)}
              <span className={styles.precioUnit}>/m²</span>
            </p>
            {product.descripcion && (
              <p className={styles.descripcion}>{product.descripcion}</p>
            )}

            <div className={styles.divider} />

            {/* Guía de medidas */}
            <div className={styles.guia}>
              <h3 className={styles.guiaTitulo}>
                <AlertCircle size={16} />
                ¿Cómo tomar las medidas?
              </h3>
              <p className={styles.guiaTexto}>{guiaTexto}</p>
            </div>

            <div className={styles.divider} />

            {/* Formulario de medidas */}
            <div className={styles.medidas}>
              <h3 className={styles.medidasTitulo}>Ingresa tus medidas</h3>
              <div className={styles.medidasGrid}>
                <div className={styles.field}>
                  <label className={styles.label}>Ancho (cm)</label>
                  <input type="number" min="1" placeholder="ej: 150"
                    value={ancho}
                    onChange={e => { setAncho(e.target.value); setMedErrors(p => ({ ...p, ancho: '' })) }}
                    className={`${styles.input} ${medErrors.ancho ? styles.inputError : ''}`} />
                  {medErrors.ancho && <span className={styles.errorMsg}>{medErrors.ancho}</span>}
                </div>
                <div className={styles.field}>
                  <label className={styles.label}>Alto (cm)</label>
                  <input type="number" min="1" placeholder="ej: 220"
                    value={alto}
                    onChange={e => { setAlto(e.target.value); setMedErrors(p => ({ ...p, alto: '' })) }}
                    className={`${styles.input} ${medErrors.alto ? styles.inputError : ''}`} />
                  {medErrors.alto && <span className={styles.errorMsg}>{medErrors.alto}</span>}
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
                onClick={handleAddToCart}>
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