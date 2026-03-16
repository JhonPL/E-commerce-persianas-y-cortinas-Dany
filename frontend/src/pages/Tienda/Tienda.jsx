import { useState, useMemo, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Search, SlidersHorizontal, X } from 'lucide-react'
import ProductCard from '../../components/ProductCard/ProductCard'
import styles from './Tienda.module.css'

// Datos mock
const PRODUCTOS = [
  { producto_id: 1, nombre: 'Cortina Clásica',        precio_m2: 120000, categoria: 'Cortinas',   imagen_principal: 'https://images.unsplash.com/photo-1586105251261-72a756497a11?w=600&q=75' },
  { producto_id: 2, nombre: 'Persiana Enrollable',     precio_m2: 180000, categoria: 'Persianas',  imagen_principal: 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600&q=75' },
  { producto_id: 3, nombre: 'Panel Japonés',           precio_m2: 250000, categoria: 'Paneles',    imagen_principal: 'https://images.unsplash.com/photo-1585128903994-9788298ef4fd?w=600&q=75' },
  { producto_id: 4, nombre: 'Cortina Blackout',        precio_m2: 160000, categoria: 'Cortinas',   imagen_principal: 'https://images.unsplash.com/photo-1567225557594-88887a55d299?w=600&q=75' },
  { producto_id: 5, nombre: 'Persiana Veneciana',      precio_m2: 140000, categoria: 'Persianas',  imagen_principal: 'https://images.unsplash.com/photo-1449247709967-d4461a6a6103?w=600&q=75' },
  { producto_id: 6, nombre: 'Cortina Sheer',           precio_m2: 95000,  categoria: 'Cortinas',   imagen_principal: 'https://images.unsplash.com/photo-1615874959474-d609969a20ed?w=600&q=75' },
  { producto_id: 7, nombre: 'Persiana Zebra',          precio_m2: 200000, categoria: 'Persianas',  imagen_principal: 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600&q=75' },
  { producto_id: 8, nombre: 'Riel de Cortina',         precio_m2: 45000,  categoria: 'Accesorios', imagen_principal: 'https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=600&q=75' },
]

const CATEGORIAS = ['Todas', 'Cortinas', 'Persianas', 'Paneles', 'Accesorios']

const ORDEN_OPTS = [
  { value: 'default',    label: 'Relevancia' },
  { value: 'precio_asc', label: 'Precio: menor a mayor' },
  { value: 'precio_desc', label: 'Precio: mayor a menor' },
  { value: 'nombre',     label: 'Nombre A–Z' },
]

export default function Tienda() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [busqueda,  setBusqueda]  = useState('')
  const [categoria, setCategoria] = useState(searchParams.get('categoria') || 'Todas')
  const [orden,     setOrden]     = useState('default')
  const [filtersOpen, setFiltersOpen] = useState(false)

  // Sync URL param → estado
  useEffect(() => {
    const cat = searchParams.get('categoria')
    if (cat) setCategoria(cat)
  }, [searchParams])

  // Filtrar y ordenar
  const productosFiltrados = useMemo(() => {
    let result = PRODUCTOS

    if (categoria !== 'Todas') {
      result = result.filter(p => p.categoria === categoria)
    }

    if (busqueda.trim()) {
      const q = busqueda.toLowerCase()
      result = result.filter(p =>
        p.nombre.toLowerCase().includes(q) ||
        p.categoria.toLowerCase().includes(q)
      )
    }

    switch (orden) {
      case 'precio_asc':  result = [...result].sort((a, b) => a.precio_m2 - b.precio_m2); break
      case 'precio_desc': result = [...result].sort((a, b) => b.precio_m2 - a.precio_m2); break
      case 'nombre':      result = [...result].sort((a, b) => a.nombre.localeCompare(b.nombre)); break
    }

    return result
  }, [busqueda, categoria, orden])

  const handleCategoria = (cat) => {
    setCategoria(cat)
    if (cat === 'Todas') {
      searchParams.delete('categoria')
    } else {
      searchParams.set('categoria', cat)
    }
    setSearchParams(searchParams)
  }

  const limpiarFiltros = () => {
    setBusqueda('')
    setCategoria('Todas')
    setOrden('default')
    setSearchParams({})
  }

  const hayFiltros = busqueda || categoria !== 'Todas' || orden !== 'default'

  return (
    <div className={styles.page}>
      {/* ── Header de tienda ─────────────────────────────────────────── */}
      <div className={styles.hero}>
        <div className="container">
          <p className={styles.eyebrow}>Catálogo</p>
          <h1 className={styles.title}>Nuestra Colección</h1>
          <p className={styles.subtitle}>Productos fabricados a tu medida con precios por metro cuadrado</p>
        </div>
      </div>

      {/* ── Controles ────────────────────────────────────────────────── */}
      <div className={styles.controls}>
        <div className="container">
          <div className={styles.controlsInner}>
            {/* Búsqueda */}
            <div className={styles.searchWrapper}>
              <Search size={16} className={styles.searchIcon} />
              <input
                type="text"
                placeholder="Buscar productos..."
                value={busqueda}
                onChange={e => setBusqueda(e.target.value)}
                className={styles.searchInput}
              />
              {busqueda && (
                <button className={styles.clearBtn} onClick={() => setBusqueda('')}>
                  <X size={14} />
                </button>
              )}
            </div>

            {/* Orden */}
            <select
              value={orden}
              onChange={e => setOrden(e.target.value)}
              className={styles.select}
            >
              {ORDEN_OPTS.map(o => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>

            {/* Limpiar */}
            {hayFiltros && (
              <button className={styles.limpiarBtn} onClick={limpiarFiltros}>
                <X size={14} /> Limpiar
              </button>
            )}

            {/* Toggle filtros mobile */}
            <button
              className={styles.filtersToggle}
              onClick={() => setFiltersOpen(v => !v)}
              aria-label="Filtros"
            >
              <SlidersHorizontal size={16} />
            </button>
          </div>

          {/* Categorías */}
          <div className={`${styles.categorias} ${filtersOpen ? styles.categoriasOpen : ''}`}>
            {CATEGORIAS.map(cat => (
              <button
                key={cat}
                className={`${styles.catBtn} ${categoria === cat ? styles.catActive : ''}`}
                onClick={() => handleCategoria(cat)}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ── Resultados ───────────────────────────────────────────────── */}
      <div className={styles.results}>
        <div className="container">
          <p className={styles.resultsCount}>
            {productosFiltrados.length} producto{productosFiltrados.length !== 1 ? 's' : ''}
            {categoria !== 'Todas' && ` en ${categoria}`}
          </p>

          {productosFiltrados.length > 0 ? (
            <div className={styles.grid}>
              {productosFiltrados.map(p => (
                <ProductCard key={p.producto_id} product={p} />
              ))}
            </div>
          ) : (
            <div className={styles.empty}>
              <p>No encontramos productos con esos criterios.</p>
              <button onClick={limpiarFiltros} className={styles.emptyBtn}>
                Limpiar filtros
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}