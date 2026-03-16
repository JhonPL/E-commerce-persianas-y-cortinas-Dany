import { useState, useRef, useCallback } from 'react'
import {
  Plus, Pencil, Trash2, Search, X, Check,
  ImageOff, Upload, Loader, Link, Star, StarOff
} from 'lucide-react'
import styles from './AdminProductos.module.css'

/* ── Cloudinary ───────────────────────────────────────────
   .env:
     VITE_CLOUDINARY_CLOUD_NAME=tu_cloud_name
     VITE_CLOUDINARY_UPLOAD_PRESET=cortinas_dany
   Cloudinary → Settings → Upload presets → Add (Unsigned)
   ─────────────────────────────────────────────────────── */
const CLOUD_NAME    = import.meta.env.VITE_CLOUDINARY_CLOUD_NAME    || 'tu_cloud_name'
const UPLOAD_PRESET = import.meta.env.VITE_CLOUDINARY_UPLOAD_PRESET || 'cortinas_dany'
const UPLOAD_URL    = `https://api.cloudinary.com/v1_1/${CLOUD_NAME}/image/upload`

async function subirACloudinary(file) {
  const fd = new FormData()
  fd.append('file', file)
  fd.append('upload_preset', UPLOAD_PRESET)
  fd.append('folder', 'cortinas-dany/productos')
  const res = await fetch(UPLOAD_URL, { method: 'POST', body: fd })
  if (!res.ok) throw new Error('Error al subir')
  const data = await res.json()
  return data.secure_url.replace('/upload/', '/upload/f_webp,q_auto,w_800/')
}

/* ── Constantes ───────────────────────────────────────────*/
const CATEGORIAS = ['Cortinas', 'Persianas', 'Paneles', 'Accesorios']
const EMPTY_FORM = {
  nombre: '', categoria: 'Cortinas', precio_m2: '',
  activo: true, descripcion: '',
  imagenes: [] // [{ url, principal, uploading? }]
}

const INITIAL = [
  { id: 1,  nombre: 'Cortina Clásica',        categoria: 'Cortinas',   precio_m2: 120000, activo: true,  descripcion: '', imagenes: [] },
  { id: 2,  nombre: 'Cortina Blackout',        categoria: 'Cortinas',   precio_m2: 160000, activo: true,  descripcion: '', imagenes: [] },
  { id: 3,  nombre: 'Cortina Sheer',           categoria: 'Cortinas',   precio_m2:  95000, activo: true,  descripcion: '', imagenes: [] },
  { id: 4,  nombre: 'Persiana Enrollable',     categoria: 'Persianas',  precio_m2: 180000, activo: true,  descripcion: '', imagenes: [] },
  { id: 5,  nombre: 'Persiana Veneciana',      categoria: 'Persianas',  precio_m2: 140000, activo: true,  descripcion: '', imagenes: [] },
  { id: 6,  nombre: 'Persiana Zebra',          categoria: 'Persianas',  precio_m2: 200000, activo: true,  descripcion: '', imagenes: [] },
  { id: 7,  nombre: 'Panel Japonés',           categoria: 'Paneles',    precio_m2: 250000, activo: true,  descripcion: '', imagenes: [] },
  { id: 8,  nombre: 'Panel Roller Screen',     categoria: 'Paneles',    precio_m2: 220000, activo: true,  descripcion: '', imagenes: [] },
  { id: 9,  nombre: 'Riel de Aluminio Doble',  categoria: 'Accesorios', precio_m2:  45000, activo: true,  descripcion: '', imagenes: [] },
  { id: 10, nombre: 'Bastón Decorativo',       categoria: 'Accesorios', precio_m2:  38000, activo: false, descripcion: '', imagenes: [] },
]

const fmt           = (n) => `$${Number(n).toLocaleString('es-CO')}`
const getPrincipal  = (imgs) => imgs.find(i => i.principal)?.url || imgs[0]?.url || ''

/* ══════════════════════════════════════════════════════════
   SECCIÓN DE IMÁGENES — dentro del modal de crear/editar
   ══════════════════════════════════════════════════════════*/
function SeccionImagenes({ imagenes, onChange }) {
  const fileRef  = useRef(null)
  const [urlInput,  setUrlInput]  = useState('')
  const [urlErr,    setUrlErr]    = useState('')
  const [uploading, setUploading] = useState(false)
  const [fileErr,   setFileErr]   = useState('')
  const [tab,       setTab]       = useState('archivo') // 'archivo' | 'url'

  /* ── Subir desde dispositivo ── */
  const handleFiles = useCallback(async (files) => {
    const validos = Array.from(files).filter(f => f.type.startsWith('image/') && f.size <= 8 * 1024 * 1024)
    if (!validos.length) { setFileErr('Solo imágenes hasta 8 MB'); return }
    if (imagenes.length + validos.length > 8) { setFileErr('Máximo 8 fotos'); return }
    setFileErr('')
    setUploading(true)

    // Preview local inmediato
    const previews = validos.map((f, i) => ({
      url: URL.createObjectURL(f),
      principal: imagenes.length === 0 && i === 0,
      uploading: true
    }))
    const base = [...imagenes, ...previews]
    onChange(base)

    // Subir a Cloudinary
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

  /* ── Agregar por URL ── */
  const handleAddUrl = () => {
    const url = urlInput.trim()
    if (!url) { setUrlErr('Pega una URL de imagen'); return }
    if (!/^https?:\/\/.+\.(jpg|jpeg|png|webp|gif|svg)(\?.*)?$/i.test(url)) {
      setUrlErr('URL de imagen no válida'); return
    }
    if (imagenes.length >= 8) { setUrlErr('Máximo 8 fotos'); return }
    setUrlErr('')
    const nueva = { url, principal: imagenes.length === 0 }
    onChange([...imagenes, nueva])
    setUrlInput('')
  }

  /* ── Marcar principal ── */
  const marcarPrincipal = (idx) =>
    onChange(imagenes.map((img, i) => ({ ...img, principal: i === idx })))

  /* ── Eliminar ── */
  const eliminar = (idx) => {
    const next = imagenes.filter((_, i) => i !== idx)
    if (imagenes[idx]?.principal && next.length > 0)
      next[0] = { ...next[0], principal: true }
    onChange(next)
  }

  return (
    <div className={styles.seccionImagenes}>
      <div className={styles.imgSecHeader}>
        <span className={styles.label}>Imágenes del producto</span>
        <span className={styles.imgCount}>{imagenes.length}/8</span>
      </div>

      {/* Tabs: Subir archivo / URL */}
      <div className={styles.imgTabs}>
        <button
          type="button"
          className={`${styles.imgTab} ${tab === 'archivo' ? styles.imgTabActive : ''}`}
          onClick={() => setTab('archivo')}
        >
          <Upload size={13} /> Subir desde dispositivo
        </button>
        <button
          type="button"
          className={`${styles.imgTab} ${tab === 'url' ? styles.imgTabActive : ''}`}
          onClick={() => setTab('url')}
        >
          <Link size={13} /> Pegar URL
        </button>
      </div>

      {/* Panel: subir archivo */}
      {tab === 'archivo' && (
        <div className={styles.imgTabPanel}>
          <div
            className={styles.dropZone}
            onClick={() => fileRef.current?.click()}
          >
            {uploading
              ? <><Loader size={20} className={styles.spinIcon} /><span>Subiendo a Cloudinary...</span></>
              : <><Upload size={20} className={styles.dropIcon} /><span>Haz clic o arrastra imágenes aquí</span><span className={styles.dropHint}>JPG, PNG, WEBP · Máx 8 MB · Puedes seleccionar varias</span></>
            }
          </div>
          {fileErr && <span className={styles.fieldErr}>{fileErr}</span>}
          <input
            ref={fileRef} type="file" accept="image/*" multiple
            className={styles.fileHidden}
            onChange={e => handleFiles(e.target.files)}
          />
        </div>
      )}

      {/* Panel: URL */}
      {tab === 'url' && (
        <div className={styles.imgTabPanel}>
          <div className={styles.urlRow}>
            <input
              className={`${styles.input} ${urlErr ? styles.inputErr : ''}`}
              placeholder="https://ejemplo.com/imagen.jpg"
              value={urlInput}
              onChange={e => { setUrlInput(e.target.value); setUrlErr('') }}
              onKeyDown={e => e.key === 'Enter' && handleAddUrl()}
            />
            <button type="button" className={styles.btnAddUrl} onClick={handleAddUrl}>
              <Plus size={14} /> Agregar
            </button>
          </div>
          {urlErr && <span className={styles.fieldErr}>{urlErr}</span>}
        </div>
      )}

      {/* Galería de fotos agregadas */}
      {imagenes.length > 0 && (
        <div className={styles.galeria}>
          {imagenes.map((img, idx) => (
            <div
              key={idx}
              className={`${styles.galeriaItem} ${img.principal ? styles.galeriaItemPrincipal : ''}`}
            >
              {/* Thumb */}
              <div className={styles.galeriaThumb}>
                {img.uploading
                  ? <div className={styles.galeriaLoading}><Loader size={16} className={styles.spinIcon} /></div>
                  : <img src={img.url} alt={`img-${idx}`} />
                }
              </div>

              {/* Badge principal */}
              {img.principal && <span className={styles.principalBadge}>Principal</span>}

              {/* Controles */}
              {!img.uploading && (
                <div className={styles.galeriaControls}>
                  <button
                    type="button"
                    className={`${styles.galeriaBtn} ${img.principal ? styles.galeriaBtnOn : ''}`}
                    onClick={() => marcarPrincipal(idx)}
                    title={img.principal ? 'Imagen principal' : 'Marcar como principal'}
                  >
                    {img.principal ? <Star size={12} fill="#8fc263" /> : <StarOff size={12} />}
                  </button>
                  <button
                    type="button"
                    className={`${styles.galeriaBtn} ${styles.galeriaBtnDel}`}
                    onClick={() => eliminar(idx)}
                    title="Eliminar"
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
              )}
            </div>
          ))}

          {/* Celda agregar más */}
          {imagenes.length < 8 && (
            <div
              className={styles.galeriaAdd}
              onClick={() => { setTab('archivo'); fileRef.current?.click() }}
              title="Agregar más fotos"
            >
              <Plus size={18} />
            </div>
          )}
        </div>
      )}

      {imagenes.length > 0 && (
        <p className={styles.imgHint}>
          <Star size={11} /> Haz clic en ⭐ para elegir la imagen principal que se mostrará en la tienda
        </p>
      )}
    </div>
  )
}

/* ══════════════════════════════════════════════════════════
   MODAL: Crear / Editar producto (con imágenes integradas)
   ══════════════════════════════════════════════════════════*/
function ModalProducto({ modo, form, errors, onChange, onClose, onSave }) {
  return (
    <div className={styles.overlay}>
      <div className={`${styles.modal} ${styles.modalLg}`}>

        <div className={styles.modalHeader}>
          <h2 className={styles.modalTitle}>
            {modo === 'new' ? 'Nuevo producto' : 'Editar producto'}
          </h2>
          <button className={styles.modalClose} onClick={onClose}><X size={18} /></button>
        </div>

        <div className={styles.modalBody}>
          <div className={styles.formGrid}>

            {/* Nombre */}
            <div className={styles.field}>
              <label className={styles.label}>Nombre <span className={styles.req}>*</span></label>
              <input
                className={`${styles.input} ${errors.nombre ? styles.inputErr : ''}`}
                value={form.nombre}
                onChange={e => onChange('nombre', e.target.value)}
                placeholder="Ej: Cortina Clásica"
              />
              {errors.nombre && <span className={styles.fieldErr}>{errors.nombre}</span>}
            </div>

            {/* Categoría */}
            <div className={styles.field}>
              <label className={styles.label}>Categoría</label>
              <select
                className={styles.input}
                value={form.categoria}
                onChange={e => onChange('categoria', e.target.value)}
              >
                {CATEGORIAS.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>

            {/* Precio */}
            <div className={styles.field}>
              <label className={styles.label}>Precio por m² (COP) <span className={styles.req}>*</span></label>
              <input
                className={`${styles.input} ${errors.precio_m2 ? styles.inputErr : ''}`}
                type="number" min="0"
                value={form.precio_m2}
                onChange={e => onChange('precio_m2', e.target.value)}
                placeholder="Ej: 150000"
              />
              {errors.precio_m2 && <span className={styles.fieldErr}>{errors.precio_m2}</span>}
            </div>

            {/* Activo */}
            <div className={styles.field} style={{ justifyContent: 'flex-end' }}>
              <label className={styles.checkLabel}>
                <input
                  type="checkbox"
                  checked={form.activo}
                  onChange={e => onChange('activo', e.target.checked)}
                  className={styles.checkbox}
                />
                Visible en tienda
              </label>
            </div>

            {/* Descripción */}
            <div className={`${styles.field} ${styles.fieldFull}`}>
              <label className={styles.label}>Descripción</label>
              <textarea
                className={`${styles.input} ${styles.textarea}`}
                value={form.descripcion}
                onChange={e => onChange('descripcion', e.target.value)}
                placeholder="Describe el producto, materiales, uso recomendado..."
                rows={2}
              />
            </div>

            {/* IMÁGENES — sección completa */}
            <div className={`${styles.field} ${styles.fieldFull}`}>
              <SeccionImagenes
                imagenes={form.imagenes}
                onChange={(imgs) => onChange('imagenes', imgs)}
              />
            </div>

          </div>
        </div>

        <div className={styles.modalFooter}>
          <button className={styles.btnSecondary} onClick={onClose}>Cancelar</button>
          <button className={styles.btnPrimary} onClick={onSave}>
            <Check size={15} />
            {modo === 'new' ? 'Crear producto' : 'Guardar cambios'}
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
  const [productos, setProductos] = useState(INITIAL)
  const [search,    setSearch]    = useState('')
  const [catFilter, setCatFilter] = useState('Todos')
  const [modal,     setModal]     = useState(null)  // null | 'new' | 'edit'
  const [modalDel,  setModalDel]  = useState(null)
  const [current,   setCurrent]   = useState(null)
  const [form,      setForm]      = useState(EMPTY_FORM)
  const [errors,    setErrors]    = useState({})

  const filtered = productos.filter(p => {
    const matchS = p.nombre.toLowerCase().includes(search.toLowerCase())
    const matchC = catFilter === 'Todos' || p.categoria === catFilter
    return matchS && matchC
  })

  const openNew  = () => { setForm({ ...EMPTY_FORM, imagenes: [] }); setErrors({}); setModal('new') }
  const openEdit = (p) => {
    setForm({
      nombre: p.nombre, categoria: p.categoria,
      precio_m2: p.precio_m2, activo: p.activo,
      descripcion: p.descripcion || '',
      imagenes: p.imagenes || []
    })
    setCurrent(p); setErrors({}); setModal('edit')
  }

  const validate = () => {
    const e = {}
    if (!form.nombre.trim()) e.nombre = 'Requerido'
    if (!form.precio_m2)     e.precio_m2 = 'Requerido'
    else if (Number(form.precio_m2) <= 0) e.precio_m2 = 'Debe ser > 0'
    setErrors(e)
    return !Object.keys(e).length
  }

  const handleSave = () => {
    if (!validate()) return
    if (modal === 'new') {
      setProductos(prev => [...prev, {
        ...form, id: Date.now(),
        precio_m2: Number(form.precio_m2)
      }])
    } else {
      setProductos(prev => prev.map(p =>
        p.id === current.id
          ? { ...p, ...form, precio_m2: Number(form.precio_m2) }
          : p
      ))
    }
    setModal(null)
  }

  const handleDelete  = () => { setProductos(prev => prev.filter(p => p.id !== modalDel.id)); setModalDel(null) }
  const toggleActivo  = (id) => setProductos(prev => prev.map(p => p.id === id ? { ...p, activo: !p.activo } : p))
  const onChange      = (k, v) => setForm(prev => ({ ...prev, [k]: v }))

  return (
    <div className={styles.page}>

      {/* Header */}
      <div className={styles.pageHeader}>
        <div>
          <h1 className={styles.pageTitle}>Productos</h1>
          <p className={styles.pageSub}>{productos.length} productos en total</p>
        </div>
        <button className={styles.btnPrimary} onClick={openNew}>
          <Plus size={16} /> Nuevo producto
        </button>
      </div>

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
          {['Todos', ...CATEGORIAS].map(c => (
            <button key={c}
              className={`${styles.pill} ${catFilter === c ? styles.pillActive : ''}`}
              onClick={() => setCatFilter(c)}
            >{c}</button>
          ))}
        </div>
      </div>

      {/* Tabla */}
      <div className={styles.tableCard}>
        <div className={styles.tableWrapper}>
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
                const imgPrincipal = getPrincipal(p.imagenes)
                return (
                  <tr key={p.id}>
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
                          {p.imagenes.length > 0 && (
                            <span className={styles.productImgCount}>
                              {p.imagenes.length} foto{p.imagenes.length > 1 ? 's' : ''}
                            </span>
                          )}
                        </div>
                      </div>
                    </td>
                    <td><span className={styles.catBadge}>{p.categoria}</span></td>
                    <td className={styles.tdGreen}>{fmt(p.precio_m2)}</td>
                    <td>
                      <button
                        className={`${styles.toggleBtn} ${p.activo ? styles.toggleOn : styles.toggleOff}`}
                        onClick={() => toggleActivo(p.id)}
                      >
                        {p.activo ? 'Activo' : 'Inactivo'}
                      </button>
                    </td>
                    <td>
                      <div className={styles.actions}>
                        <button className={styles.actionBtn} onClick={() => openEdit(p)} title="Editar">
                          <Pencil size={14} />
                        </button>
                        <button className={`${styles.actionBtn} ${styles.actionDelete}`} onClick={() => setModalDel(p)} title="Eliminar">
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal crear / editar */}
      {(modal === 'new' || modal === 'edit') && (
        <ModalProducto
          modo={modal}
          form={form}
          errors={errors}
          onChange={onChange}
          onClose={() => setModal(null)}
          onSave={handleSave}
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
              <button className={styles.btnDanger} onClick={handleDelete}>
                <Trash2 size={15} /> Eliminar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}