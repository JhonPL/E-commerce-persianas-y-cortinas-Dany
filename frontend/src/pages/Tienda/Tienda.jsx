import { useState, useMemo, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Search, SlidersHorizontal, X, Loader } from 'lucide-react'
import ProductCard from '../../components/ProductCard/ProductCard'
import styles from './Tienda.module.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1'

const ORDEN_OPTS = [
  { value: 'default',     label: 'Relevancia' },
  { value: 'precio_asc',  label: 'Precio: menor a mayor' },
  { value: 'precio_desc', label: 'Precio: mayor a menor' },
  { value: 'nombre',      label: 'Nombre A–Z' },
]

export default function Tienda() {
  const [searchParams, setSearchParams] = useSearchParams()

  const [productos,    setProductos]    = useState([])
  const [categorias,   setCategorias]   = useState([])
  const [loading,      setLoading]      = useState(true)
  const [error,        setError]        = useState('')
  const [busqueda,     setBusqueda]     = useState('')
  const [categoria,    setCategoria]    = useState(searchParams.get('categoria') || 'Todas')
  const [orden,        setOrden]        = useState('default')
  const [filtersOpen,  setFiltersOpen]  = useState(false)

  // Cargar productos y categorías al montar
  useEffect(() => {
    const cargar = async () => {
      setLoading(true); setError('')
      try {
        const [resProd, resCat] = await Promise.all([
          fetch(`${API_URL}/catalogo/productos/?page_size=100`),
          fetch(`${API_URL}/catalogo/categorias/`),
        ])
        if (!resProd.ok) throw new Error('Error al cargar productos')
        const dataProd = await resProd.json()
        const dataCat  = await resCat.json()
        setProductos(Array.isArray(dataProd) ? dataProd : dataProd.results || [])
        setCategorias(Array.isArray(dataCat)  ? dataCat  : dataCat.results  || [])
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    cargar()
  }, [])

  // Sincronizar categoría con URL param
  useEffect(() => {
    const cat = searchParams.get('categoria')
    if (cat) setCategoria(cat)
  }, [searchParams])

  // Filtrar y ordenar en el cliente
  const productosFiltrados = useMemo(() => {
    let result = [...productos]

    if (categoria !== 'Todas') {
      result = result.filter(p => p.categoria_nombre === categoria)
    }
    if (busqueda.trim()) {
      const q = busqueda.toLowerCase()
      result = result.filter(p =>
        p.nombre.toLowerCase().includes(q) ||
        p.categoria_nombre?.toLowerCase().includes(q)
      )
    }
    switch (orden) {
      case 'precio_asc':  result.sort((a, b) => a.precio_m2 - b.precio_m2); break
      case 'precio_desc': result.sort((a, b) => b.precio_m2 - a.precio_m2); break
      case 'nombre':      result.sort((a, b) => a.nombre.localeCompare(b.nombre)); break
    }
    return result
  }, [productos, busqueda, categoria, orden])

  const handleCategoria = (cat) => {
    setCategoria(cat)
    if (cat === 'Todas') searchParams.delete('categoria')
    else searchParams.set('categoria', cat)
    setSearchParams(searchParams)
  }

  const limpiarFiltros = () => {
    setBusqueda(''); setCategoria('Todas'); setOrden('default')
    setSearchParams({})
  }

  const hayFiltros = busqueda || categoria !== 'Todas' || orden !== 'default'

  return (
    <div className={styles.page}>

      {/* Hero */}
      <div className={styles.hero}>
        <div className="container">
          <p className={styles.eyebrow}>Catálogo</p>
          <h1 className={styles.title}>Nuestra Colección</h1>
          <p className={styles.subtitle}>Productos fabricados a tu medida con precios por metro cuadrado</p>
        </div>
      </div>

      {/* Controles */}
      <div className={styles.controls}>
        <div className="container">
          <div className={styles.controlsInner}>
            <div className={styles.searchWrapper}>
              <Search size={16} className={styles.searchIcon} />
              <input type="text" placeholder="Buscar productos..."
                value={busqueda} onChange={e => setBusqueda(e.target.value)}
                className={styles.searchInput} />
              {busqueda && (
                <button className={styles.clearBtn} onClick={() => setBusqueda('')}><X size={14} /></button>
              )}
            </div>
            <select value={orden} onChange={e => setOrden(e.target.value)} className={styles.select}>
              {ORDEN_OPTS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
            {hayFiltros && (
              <button className={styles.limpiarBtn} onClick={limpiarFiltros}>
                <X size={14} /> Limpiar
              </button>
            )}
            <button className={styles.filtersToggle} onClick={() => setFiltersOpen(v => !v)}>
              <SlidersHorizontal size={16} />
            </button>
          </div>

          {/* Pills de categorías — dinámicas del backend */}
          <div className={`${styles.categorias} ${filtersOpen ? styles.categoriasOpen : ''}`}>
            <button
              className={`${styles.catBtn} ${categoria === 'Todas' ? styles.catActive : ''}`}
              onClick={() => handleCategoria('Todas')}>
              Todas
            </button>
            {categorias.map(cat => (
              <button key={cat.categoria_id}
                className={`${styles.catBtn} ${categoria === cat.nombre ? styles.catActive : ''}`}
                onClick={() => handleCategoria(cat.nombre)}>
                {cat.nombre}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Resultados */}
      <div className={styles.results}>
        <div className="container">

          {loading && (
            <div className={styles.loadingState}>
              <Loader size={28} className={styles.spinIcon} />
              <p>Cargando productos...</p>
            </div>
          )}

          {error && !loading && (
            <div className={styles.errorState}>
              <p>{error}</p>
              <button onClick={() => window.location.reload()} className={styles.emptyBtn}>
                Reintentar
              </button>
            </div>
          )}

          {!loading && !error && (
            <>
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
            </>
          )}
        </div>
      </div>
    </div>
  )
}