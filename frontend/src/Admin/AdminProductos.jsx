import { useState, useRef, useCallback, useEffect } from 'react'
import {
  Plus, Pencil, Trash2, Search, X, Check,
  ImageOff, Upload, Loader, Link, Star, StarOff, RefreshCw
} from 'lucide-react'
import styles from './AdminProductos.module.css'

/* ── Config ───────────────────────────────────────────────*/
const API_URL       = import.meta.env.VITE_API_URL            || 'http://127.0.0.1:8000/api/v1'
const CLOUD_NAME    = import.meta.env.VITE_CLOUDINARY_CLOUD_NAME    || 'tu_cloud_name'
const UPLOAD_PRESET = import.meta.env.VITE_CLOUDINARY_UPLOAD_PRESET || 'cortinas_dany'
const UPLOAD_URL    = `https://api.cloudinary.com/v1_1/${CLOUD_NAME}/image/upload`

const authHeaders = () => ({
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
})

/* ── Helpers ──────────────────────────────────────────────*/
const fmt          = (n) => `$${Number(n).toLocaleString('es-CO')}`
const getPrincipal = (imagenPrincipal) => imagenPrincipal || ''

async function subirACloudinary(file) {
  const fd = new FormData()
  fd.append('file', file)
  fd.append('upload_preset', UPLOAD_PRESET)
  fd.append('folder', 'cortinas-dany/productos')
  const res  = await fetch(UPLOAD_URL, { method: 'POST', body: fd })
  if (!res.ok) throw new Error('Error al subir imagen')
  const data = await res.json()
  return data.secure_url.replace('/upload/', '/upload/f_webp,q_auto,w_800/')
}

const EMPTY_FORM = {
  nombre: '', categoria_id: '', precio_m2: '',
  activo: true, descripcion: '',
  imagenes: [],   // [{ url, es_principal, uploading? }]
}

/* ══════════════════════════════════════════════════════════
   SECCIÓN DE IMÁGENES
   ══════════════════════════════════════════════════════════*/
function SeccionImagenes({ imagenes, onChange }) {
  const fileRef = useRef(null)
  const [tab,       setTab]       = useState('archivo')
  const [urlInput,  setUrlInput]  = useState('')
  const [urlErr,    setUrlErr]    = useState('')
  const [uploading, setUploading] = useState(false)
  const [fileErr,   setFileErr]   = useState('')

  const handleFiles = useCallback(async (files) => {
    const validos = Array.from(files).filter(f => f.type.startsWith('image/') && f.size <= 8 * 1024 * 1024)
    if (!validos.length) { setFileErr('Solo imágenes hasta 8 MB'); return }
    if (imagenes.length + validos.length > 8) { setFileErr('Máximo 8 fotos'); return }
    setFileErr(''); setUploading(true)

    const previews = validos.map((f, i) => ({
      url: URL.createObjectURL(f),
      es_principal: imagenes.length === 0 && i === 0,
      uploading: true,
    }))
    const base = [...imagenes, ...previews]
    onChange(base)

    const results = await Promise.allSettled(validos.map(f => subirACloudinary(f)))
    const updated = [...base]
    const offset  = imagenes.length
    results.forEach((r, i) => {
      if (r.status === 'fulfilled') {
        updated[offset + i] = { ...updated[offset + i], url: r.value, uploading: false }
      } else {
        updated.splice(offset + i, 1)
      }
    })
    onChange(updated)
    setUploading(false)
  }, [imagenes, onChange])

  const handleAddUrl = () => {
    const url = urlInput.trim()
    if (!url) { setUrlErr('Pega una URL'); return }
    if (!/^https?:\/\/.+\.(jpg|jpeg|png|webp|gif|svg)(\?.*)?$/i.test(url)) { setUrlErr('URL inválida'); return }
    if (imagenes.length >= 8) { setUrlErr('Máximo 8 fotos'); return }
    setUrlErr('')
    onChange([...imagenes, { url, es_principal: imagenes.length === 0 }])
    setUrlInput('')
  }

  const marcarPrincipal = (idx) =>
    onChange(imagenes.map((img, i) => ({ ...img, es_principal: i === idx })))

  const eliminar = (idx) => {
    const next = imagenes.filter((_, i) => i !== idx)
    if (imagenes[idx]?.es_principal && next.length > 0)
      next[0] = { ...next[0], es_principal: true }
    onChange(next)
  }

  return (
    <div className={styles.seccionImagenes}>
      <div className={styles.imgSecHeader}>
        <span className={styles.label}>Imágenes del producto</span>
        <span className={styles.imgCount}>{imagenes.length}/8</span>
      </div>

      <div className={styles.imgTabs}>
        <button type="button"
          className={`${styles.imgTab} ${tab === 'archivo' ? styles.imgTabActive : ''}`}
          onClick={() => setTab('archivo')}>
          <Upload size={13} /> Subir desde dispositivo
        </button>
        <button type="button"
          className={`${styles.imgTab} ${tab === 'url' ? styles.imgTabActive : ''}`}
          onClick={() => setTab('url')}>
          <Link size={13} /> Pegar URL
        </button>
      </div>

      {tab === 'archivo' && (
        <div className={styles.imgTabPanel}>
          <div className={styles.dropZone} onClick={() => fileRef.current?.click()}>
            {uploading
              ? <><Loader size={20} className={styles.spinIcon} /><span>Subiendo a Cloudinary...</span></>
              : <><Upload size={20} className={styles.dropIcon} /><span>Haz clic o arrastra imágenes aquí</span><span className={styles.dropHint}>JPG, PNG, WEBP · Máx 8 MB · Puedes seleccionar varias</span></>
            }
          </div>
          {fileErr && <span className={styles.fieldErr}>{fileErr}</span>}
          <input ref={fileRef} type="file" accept="image/*" multiple
            className={styles.fileHidden}
            onChange={e => handleFiles(e.target.files)} />
        </div>
      )}

      {tab === 'url' && (
        <div className={styles.imgTabPanel}>
          <div className={styles.urlRow}>
            <input className={`${styles.input} ${urlErr ? styles.inputErr : ''}`}
              placeholder="https://ejemplo.com/imagen.jpg"
              value={urlInput}
              onChange={e => { setUrlInput(e.target.value); setUrlErr('') }}
              onKeyDown={e => e.key === 'Enter' && handleAddUrl()} />
            <button type="button" className={styles.btnAddUrl} onClick={handleAddUrl}>
              <Plus size={14} /> Agregar
            </button>
          </div>
          {urlErr && <span className={styles.fieldErr}>{urlErr}</span>}
        </div>
      )}

      {imagenes.length > 0 && (
        <div className={styles.galeria}>
          {imagenes.map((img, idx) => (
            <div key={idx} className={`${styles.galeriaItem} ${img.es_principal ? styles.galeriaItemPrincipal : ''}`}>
              <div className={styles.galeriaThumb}>
                {img.uploading
                  ? <div className={styles.galeriaLoading}><Loader size={16} className={styles.spinIcon} /></div>
                  : <img src={img.url} alt={`img-${idx}`} />
                }
              </div>
              {img.es_principal && <span className={styles.principalBadge}>Principal</span>}
              {!img.uploading && (
                <div className={styles.galeriaControls}>
                  <button type="button"
                    className={`${styles.galeriaBtn} ${img.es_principal ? styles.galeriaBtnOn : ''}`}
                    onClick={() => marcarPrincipal(idx)}
                    title={img.es_principal ? 'Imagen principal' : 'Marcar como principal'}>
                    {img.es_principal ? <Star size={12} fill="#8fc263" /> : <StarOff size={12} />}
                  </button>
                  <button type="button"
                    className={`${styles.galeriaBtn} ${styles.galeriaBtnDel}`}
                    onClick={() => eliminar(idx)} title="Eliminar">
                    <Trash2 size={12} />
                  </button>
                </div>
              )}
            </div>
          ))}
          {imagenes.length < 8 && (
            <div className={styles.galeriaAdd}
              onClick={() => { setTab('archivo'); fileRef.current?.click() }}>
              <Plus size={18} />
            </div>
          )}
        </div>
      )}

      {imagenes.length > 0 && (
        <p className={styles.imgHint}>
          <Star size={11} /> Haz clic en ⭐ para elegir la imagen principal
        </p>
      )}
    </div>
  )
}

/* ══════════════════════════════════════════════════════════
   MODAL PRODUCTO
   ══════════════════════════════════════════════════════════*/
function ModalProducto({ modo, form, errors, categorias, onChange, onClose, onSave, saving }) {
  return (
    <div className={styles.overlay}>
      <div className={`${styles.modal} ${styles.modalLg}`}>
        <div className={styles.modalHeader}>
          <h2 className={styles.modalTitle}>{modo === 'new' ? 'Nuevo producto' : 'Editar producto'}</h2>
          <button className={styles.modalClose} onClick={onClose}><X size={18} /></button>
        </div>
        <div className={styles.modalBody}>
          {errors.global && <p className={styles.globalErr}>{errors.global}</p>}
          <div className={styles.formGrid}>

            <div className={styles.field}>
              <label className={styles.label}>Nombre <span className={styles.req}>*</span></label>
              <input className={`${styles.input} ${errors.nombre ? styles.inputErr : ''}`}
                value={form.nombre} onChange={e => onChange('nombre', e.target.value)}
                placeholder="Ej: Cortina Clásica" />
              {errors.nombre && <span className={styles.fieldErr}>{errors.nombre}</span>}
            </div>

            <div className={styles.field}>
              <label className={styles.label}>Categoría <span className={styles.req}>*</span></label>
              <select className={`${styles.input} ${errors.categoria_id ? styles.inputErr : ''}`}
                value={form.categoria_id} onChange={e => onChange('categoria_id', e.target.value)}>
                <option value="">Selecciona una categoría</option>
                {categorias.map(c => (
                  <option key={c.categoria_id} value={c.categoria_id}>{c.nombre}</option>
                ))}
              </select>
              {errors.categoria_id && <span className={styles.fieldErr}>{errors.categoria_id}</span>}
            </div>

            <div className={styles.field}>
              <label className={styles.label}>Precio por m² (COP) <span className={styles.req}>*</span></label>
              <input className={`${styles.input} ${errors.precio_m2 ? styles.inputErr : ''}`}
                type="number" min="0"
                value={form.precio_m2} onChange={e => onChange('precio_m2', e.target.value)}
                placeholder="Ej: 150000" />
              {errors.precio_m2 && <span className={styles.fieldErr}>{errors.precio_m2}</span>}
            </div>

            <div className={styles.field} style={{ justifyContent: 'flex-end' }}>
              <label className={styles.checkLabel}>
                <input type="checkbox" checked={form.activo}
                  onChange={e => onChange('activo', e.target.checked)}
                  className={styles.checkbox} />
                Visible en tienda
              </label>
            </div>

            <div className={`${styles.field} ${styles.fieldFull}`}>
              <label className={styles.label}>Descripción</label>
              <textarea className={`${styles.input} ${styles.textarea}`}
                value={form.descripcion} onChange={e => onChange('descripcion', e.target.value)}
                placeholder="Materiales, usos recomendados..." rows={2} />
            </div>

            <div className={`${styles.field} ${styles.fieldFull}`}>
              <SeccionImagenes
                imagenes={form.imagenes}
                onChange={(imgs) => onChange('imagenes', imgs)} />
            </div>

          </div>
        </div>
        <div className={styles.modalFooter}>
          <button className={styles.btnSecondary} onClick={onClose}>Cancelar</button>
          <button className={styles.btnPrimary} onClick={onSave} disabled={saving}>
            <Check size={15} />
            {saving ? 'Guardando...' : modo === 'new' ? 'Crear producto' : 'Guardar cambios'}
          </button>
        </div>
      </div>
    </div>
  )
}

/* ══════════════════════════════════════════════════════════
   PÁGINA PRINCIPAL
   ══════════════════════════════════════════════════════════*/
export default function AdminProductos() {
  const [productos,  setProductos]  = useState([])
  const [categorias, setCategorias] = useState([])
  const [loading,    setLoading]    = useState(true)
  const [error,      setError]      = useState('')
  const [search,     setSearch]     = useState('')
  const [catFilter,  setCatFilter]  = useState('Todos')
  const [modal,      setModal]      = useState(null)
  const [modalDel,   setModalDel]   = useState(null)
  const [current,    setCurrent]    = useState(null)
  const [form,       setForm]       = useState(EMPTY_FORM)
  const [errors,     setErrors]     = useState({})
  const [saving,     setSaving]     = useState(false)

  /* ── Cargar datos ── */
  const cargarProductos = async () => {
    setLoading(true); setError('')
    try {
      // Admin necesita ver todos (activos e inactivos)
      const res = await fetch(`${API_URL}/catalogo/productos/?page_size=100`, {
        headers: authHeaders(),
      })
      if (!res.ok) throw new Error('No se pudieron cargar los productos')
      const data = await res.json()
      setProductos(Array.isArray(data) ? data : data.results || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const cargarCategorias = async () => {
    try {
      const res  = await fetch(`${API_URL}/catalogo/categorias/`)
      const data = await res.json()
      setCategorias(Array.isArray(data) ? data : data.results || [])
    } catch { /* silencioso */ }
  }

  useEffect(() => {
    cargarProductos()
    cargarCategorias()
  }, [])

  /* ── Filtrado local ── */
  const filtered = productos.filter(p => {
    const matchS = p.nombre.toLowerCase().includes(search.toLowerCase())
    const matchC = catFilter === 'Todos' || p.categoria_nombre === catFilter || String(p.categoria) === catFilter
    return matchS && matchC
  })

  /* ── Abrir modales ── */
  const openNew  = () => {
    setForm({ ...EMPTY_FORM, categoria_id: categorias[0]?.categoria_id || '' })
    setErrors({}); setModal('new')
  }
  const openEdit = async (p) => {
    try {
      // Fetch completo del producto para obtener descripcion e imagenes
      const res = await fetch(`${API_URL}/catalogo/productos/${p.producto_id}/`, {
        headers: authHeaders(),
      })
      if (!res.ok) throw new Error('No se pudo cargar el producto')
      const fullData = await res.json()

      setForm({
        nombre:       fullData.nombre,
        categoria_id: fullData.categoria,
        precio_m2:    fullData.precio_m2,
        activo:       fullData.activo,
        descripcion:  fullData.descripcion || '',
        imagenes:     (fullData.imagenes || []).map(img => ({
          url:          img.url,
          es_principal: img.es_principal,
          imagen_id:    img.imagen_id,
        })),
      })
      setCurrent(fullData); setErrors({}); setModal('edit')
    } catch (err) {
      setError(err.message)
    }
  }

  /* ── Validar ── */
  const validate = () => {
    const e = {}
    if (!form.nombre.trim())  e.nombre       = 'Requerido'
    if (!form.categoria_id)   e.categoria_id = 'Selecciona una categoría'
    if (!form.precio_m2)      e.precio_m2    = 'Requerido'
    else if (Number(form.precio_m2) <= 0) e.precio_m2 = 'Debe ser > 0'
    setErrors(e)
    return !Object.keys(e).length
  }

  /* ── Guardar producto (crear / editar) ── */
  const handleSave = async () => {
    if (!validate()) return
    setSaving(true)
    try {
      const esNuevo = modal === 'new'
      const url     = esNuevo
        ? `${API_URL}/catalogo/productos/`
        : `${API_URL}/catalogo/productos/${current.producto_id}/`

      // 1. Guardar datos del producto
      const body = {
        nombre:      form.nombre,
        descripcion: form.descripcion,
        precio_m2:   Number(form.precio_m2),
        categoria:   Number(form.categoria_id),
        activo:      form.activo,
      }

      const res  = await fetch(url, {
        method:  esNuevo ? 'POST' : 'PUT',
        headers: authHeaders(),
        body:    JSON.stringify(body),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(Object.values(data)[0]?.[0] || 'Error al guardar')

      const productoId = data.producto_id

      // 2. Sincronizar imágenes via endpoint subir_imagen
      const imagenesNuevas = form.imagenes.filter(img => !img.imagen_id && !img.uploading)
      for (const img of imagenesNuevas) {
        await fetch(`${API_URL}/catalogo/productos/${productoId}/subir_imagen/`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${sessionStorage.getItem('token') || ''}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ url: img.url, es_principal: img.es_principal }),
        })
      }

      await cargarProductos()
      setModal(null)
    } catch (err) {
      setErrors(prev => ({ ...prev, global: err.message }))
    } finally {
      setSaving(false)
    }
  }

  /* ── Eliminar ── */
  const handleDelete = async () => {
    setSaving(true)
    try {
      const res = await fetch(
        `${API_URL}/catalogo/productos/${modalDel.producto_id}/`,
        { method: 'DELETE', headers: authHeaders() }
      )
      if (!res.ok && res.status !== 204) throw new Error('No se pudo eliminar')
      await cargarProductos()
      setModalDel(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  /* ── Toggle activo ── */
  const toggleActivo = async (p) => {
    try {
      await fetch(`${API_URL}/catalogo/productos/${p.producto_id}/`, {
        method:  'PATCH',
        headers: authHeaders(),
        body:    JSON.stringify({ activo: !p.activo }),
      })
      await cargarProductos()
    } catch {
      setError('No se pudo cambiar el estado')
    }
  }

  const onChange = (k, v) => setForm(prev => ({ ...prev, [k]: v }))

  return (
    <div className={styles.page}>

      {/* Header */}
      <div className={styles.pageHeader}>
        <div>
          <h1 className={styles.pageTitle}>Productos</h1>
          <p className={styles.pageSub}>{productos.length} productos en total</p>
        </div>
        <div className={styles.headerActions}>
          <button className={styles.btnRefresh} onClick={cargarProductos} title="Recargar">
            <RefreshCw size={15} />
          </button>
          <button className={styles.btnPrimary} onClick={openNew}>
            <Plus size={16} /> Nuevo producto
          </button>
        </div>
      </div>

      {error && <p className={styles.globalErr}>{error}</p>}

      {/* Filtros */}
      <div className={styles.filters}>
        <div className={styles.searchWrapper}>
          <Search size={15} className={styles.searchIcon} />
          <input type="text" placeholder="Buscar producto..."
            value={search} onChange={e => setSearch(e.target.value)}
            className={styles.searchInput} />
          {search && <button className={styles.clearSearch} onClick={() => setSearch('')}><X size={14} /></button>}
        </div>
        <div className={styles.catPills}>
          {['Todos', ...categorias.map(c => c.nombre)].map(c => (
            <button key={c}
              className={`${styles.pill} ${catFilter === c ? styles.pillActive : ''}`}
              onClick={() => setCatFilter(c)}>{c}
            </button>
          ))}
        </div>
      </div>

      {/* Tabla */}
      <div className={styles.tableCard}>
        <div className={styles.tableWrapper}>
          {loading ? (
            <p className={styles.loadingMsg}>Cargando productos...</p>
          ) : (
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Producto</th>
                  <th>Categoría</th>
                  <th>Precio / m²</th>
                  <th>Estado</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 && (
                  <tr><td colSpan={5} className={styles.empty}>Sin resultados</td></tr>
                )}
                {filtered.map(p => {
                  const imgPrincipal = getPrincipal(p.imagen_principal)
                  return (
                    <tr key={p.producto_id}>
                      <td>
                        <div className={styles.productCell}>
                          <div className={styles.productThumb}>
                            {imgPrincipal
                              ? <img src={imgPrincipal} alt={p.nombre} />
                              : <ImageOff size={15} />
                            }
                          </div>
                          <div>
                            <span className={styles.productNombre}>{p.nombre}</span>
                            {p.imagenes?.length > 0 && (
                              <span className={styles.productImgCount}>
                                {p.imagenes.length} foto{p.imagenes.length > 1 ? 's' : ''}
                              </span>
                            )}
                          </div>
                        </div>
                      </td>
                      <td><span className={styles.catBadge}>{p.categoria_nombre}</span></td>
                      <td className={styles.tdGreen}>{fmt(p.precio_m2)}</td>
                      <td>
                        <button
                          className={`${styles.toggleBtn} ${p.activo ? styles.toggleOn : styles.toggleOff}`}
                          onClick={() => toggleActivo(p)}>
                          {p.activo ? 'Activo' : 'Inactivo'}
                        </button>
                      </td>
                      <td>
                        <div className={styles.actions}>
                          <button className={styles.actionBtn} onClick={() => openEdit(p)} title="Editar">
                            <Pencil size={14} />
                          </button>
                          <button className={`${styles.actionBtn} ${styles.actionDelete}`}
                            onClick={() => setModalDel(p)} title="Eliminar">
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Modal crear / editar */}
      {(modal === 'new' || modal === 'edit') && (
        <ModalProducto
          modo={modal}
          form={form}
          errors={errors}
          categorias={categorias}
          onChange={onChange}
          onClose={() => setModal(null)}
          onSave={handleSave}
          saving={saving}
        />
      )}

      {/* Modal eliminar */}
      {modalDel && (
        <div className={styles.overlay}>
          <div className={`${styles.modal} ${styles.modalSm}`}>
            <div className={styles.modalHeader}>
              <h2 className={styles.modalTitle}>Eliminar producto</h2>
              <button className={styles.modalClose} onClick={() => setModalDel(null)}><X size={18} /></button>
            </div>
            <div className={styles.modalBody}>
              <p className={styles.deleteMsg}>
                ¿Seguro que deseas eliminar <strong>"{modalDel.nombre}"</strong>?<br />
                Esta acción no se puede deshacer.
              </p>
            </div>
            <div className={styles.modalFooter}>
              <button className={styles.btnSecondary} onClick={() => setModalDel(null)}>Cancelar</button>
              <button className={styles.btnDanger} onClick={handleDelete} disabled={saving}>
                <Trash2 size={15} /> {saving ? 'Eliminando...' : 'Eliminar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}