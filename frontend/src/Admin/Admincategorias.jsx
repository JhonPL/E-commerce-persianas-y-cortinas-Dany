import { useState, useEffect } from 'react'
import { Plus, Pencil, Trash2, X, Check, Search, Tag } from 'lucide-react'
import styles from './AdminCategorias.module.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1'

function getToken() {
  return localStorage.getItem('token') || ''
}

const authHeaders = () => ({
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${getToken()}`,
})

const EMPTY_FORM = { nombre: '', descripcion: '', activo: true }

export default function AdminCategorias() {
  const [categorias,  setCategorias]  = useState([])
  const [loading,     setLoading]     = useState(true)
  const [error,       setError]       = useState('')
  const [search,      setSearch]      = useState('')
  const [modal,       setModal]       = useState(null)   // null | 'new' | 'edit'
  const [modalDel,    setModalDel]    = useState(null)
  const [current,     setCurrent]     = useState(null)
  const [form,        setForm]        = useState(EMPTY_FORM)
  const [formErrors,  setFormErrors]  = useState({})
  const [saving,      setSaving]      = useState(false)

  /* ── Cargar categorías ── */
  const cargar = async () => {
    setLoading(true)
    setError('')
    try {
      // Usamos el endpoint público (sin JWT) para listar
      const res = await fetch(`${API_URL}/catalogo/categorias/`)
      if (!res.ok) throw new Error('No se pudieron cargar las categorías')
      const data = await res.json()
      // DRF puede devolver { results: [...] } con paginación o directo []
      setCategorias(Array.isArray(data) ? data : data.results || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { cargar() }, [])

  const filtered = categorias.filter(c =>
    c.nombre.toLowerCase().includes(search.toLowerCase())
  )

  /* ── Abrir modales ── */
  const openNew  = () => { setForm(EMPTY_FORM); setFormErrors({}); setModal('new') }
  const openEdit = (c) => {
    setForm({ nombre: c.nombre, descripcion: c.descripcion || '', activo: c.activo })
    setCurrent(c); setFormErrors({}); setModal('edit')
  }

  /* ── Validar ── */
  const validate = () => {
    const e = {}
    if (!form.nombre.trim()) e.nombre = 'Requerido'
    setFormErrors(e)
    return !Object.keys(e).length
  }

  /* ── Guardar (crear / editar) ── */
  const handleSave = async () => {
    if (!validate()) return
    setSaving(true)
    try {
      const esNueva = modal === 'new'
      const url     = esNueva
        ? `${API_URL}/catalogo/categorias/`
        : `${API_URL}/catalogo/categorias/${current.categoria_id}/`

      const res = await fetch(url, {
        method:  esNueva ? 'POST' : 'PUT',
        headers: authHeaders(),
        body:    JSON.stringify(form),
      })

      if (!res.ok) {
        const data = await res.json()
        throw new Error(Object.values(data)[0]?.[0] || 'Error al guardar')
      }

      await cargar()
      setModal(null)
    } catch (err) {
      setFormErrors({ global: err.message })
    } finally {
      setSaving(false)
    }
  }

  /* ── Eliminar ── */
  const handleDelete = async () => {
    setSaving(true)
    try {
      const res = await fetch(
        `${API_URL}/catalogo/categorias/${modalDel.categoria_id}/`,
        { method: 'DELETE', headers: authHeaders() }
      )
      if (!res.ok && res.status !== 204) throw new Error('No se pudo eliminar')
      await cargar()
      setModalDel(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  /* ── Toggle activo ── */
  const toggleActivo = async (cat) => {
    try {
      await fetch(`${API_URL}/catalogo/categorias/${cat.categoria_id}/`, {
        method:  'PATCH',
        headers: authHeaders(),
        body:    JSON.stringify({ activo: !cat.activo }),
      })
      await cargar()
    } catch {
      setError('No se pudo actualizar el estado')
    }
  }

  return (
    <div className={styles.page}>

      {/* Header */}
      <div className={styles.pageHeader}>
        <div>
          <h1 className={styles.pageTitle}>Categorías</h1>
          <p className={styles.pageSub}>{categorias.length} categorías registradas</p>
        </div>
        <button className={styles.btnPrimary} onClick={openNew}>
          <Plus size={16} /> Nueva categoría
        </button>
      </div>

      {error && <p className={styles.errorMsg}>{error}</p>}

      {/* Búsqueda */}
      <div className={styles.searchWrapper}>
        <Search size={15} className={styles.searchIcon} />
        <input
          type="text" placeholder="Buscar categoría..."
          value={search} onChange={e => setSearch(e.target.value)}
          className={styles.searchInput}
        />
        {search && <button className={styles.clearSearch} onClick={() => setSearch('')}><X size={14} /></button>}
      </div>

      {/* Tabla */}
      <div className={styles.tableCard}>
        <div className={styles.tableWrapper}>
          {loading ? (
            <p className={styles.loadingMsg}>Cargando categorías...</p>
          ) : (
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Categoría</th>
                  <th>Descripción</th>
                  <th>Productos</th>
                  <th>Estado</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 && (
                  <tr><td colSpan={5} className={styles.empty}>Sin resultados</td></tr>
                )}
                {filtered.map(c => (
                  <tr key={c.categoria_id}>
                    <td>
                      <div className={styles.catCell}>
                        <div className={styles.catIcon}><Tag size={14} /></div>
                        <span className={styles.catNombre}>{c.nombre}</span>
                      </div>
                    </td>
                    <td className={styles.tdMuted}>
                      {c.descripcion || <span className={styles.tdEmpty}>Sin descripción</span>}
                    </td>
                    <td>
                      <span className={styles.countBadge}>
                        {c.productos_count ?? '—'}
                      </span>
                    </td>
                    <td>
                      <button
                        className={`${styles.toggleBtn} ${c.activo ? styles.toggleOn : styles.toggleOff}`}
                        onClick={() => toggleActivo(c)}
                      >
                        {c.activo ? 'Activa' : 'Inactiva'}
                      </button>
                    </td>
                    <td>
                      <div className={styles.actions}>
                        <button className={styles.actionBtn} onClick={() => openEdit(c)} title="Editar">
                          <Pencil size={14} />
                        </button>
                        <button
                          className={`${styles.actionBtn} ${styles.actionDelete}`}
                          onClick={() => setModalDel(c)}
                          title="Eliminar"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Modal crear / editar */}
      {modal && (
        <div className={styles.overlay}>
          <div className={styles.modal}>
            <div className={styles.modalHeader}>
              <h2 className={styles.modalTitle}>
                {modal === 'new' ? 'Nueva categoría' : 'Editar categoría'}
              </h2>
              <button className={styles.modalClose} onClick={() => setModal(null)}><X size={18} /></button>
            </div>
            <div className={styles.modalBody}>

              {formErrors.global && <p className={styles.errorMsg}>{formErrors.global}</p>}

              <div className={styles.field}>
                <label className={styles.label}>Nombre <span className={styles.req}>*</span></label>
                <input
                  className={`${styles.input} ${formErrors.nombre ? styles.inputErr : ''}`}
                  value={form.nombre}
                  onChange={e => { setForm(p => ({ ...p, nombre: e.target.value })); setFormErrors({}) }}
                  placeholder="Ej: Cortinas"
                />
                {formErrors.nombre && <span className={styles.fieldErr}>{formErrors.nombre}</span>}
              </div>

              <div className={styles.field}>
                <label className={styles.label}>Descripción</label>
                <textarea
                  className={`${styles.input} ${styles.textarea}`}
                  value={form.descripcion}
                  onChange={e => setForm(p => ({ ...p, descripcion: e.target.value }))}
                  placeholder="Descripción opcional de la categoría..."
                  rows={3}
                />
              </div>

              <label className={styles.checkLabel}>
                <input
                  type="checkbox"
                  checked={form.activo}
                  onChange={e => setForm(p => ({ ...p, activo: e.target.checked }))}
                  className={styles.checkbox}
                />
                Visible en tienda
              </label>
            </div>
            <div className={styles.modalFooter}>
              <button className={styles.btnSecondary} onClick={() => setModal(null)}>Cancelar</button>
              <button className={styles.btnPrimary} onClick={handleSave} disabled={saving}>
                <Check size={15} />
                {saving ? 'Guardando...' : modal === 'new' ? 'Crear categoría' : 'Guardar cambios'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal eliminar */}
      {modalDel && (
        <div className={styles.overlay}>
          <div className={`${styles.modal} ${styles.modalSm}`}>
            <div className={styles.modalHeader}>
              <h2 className={styles.modalTitle}>Eliminar categoría</h2>
              <button className={styles.modalClose} onClick={() => setModalDel(null)}><X size={18} /></button>
            </div>
            <div className={styles.modalBody}>
              <p className={styles.deleteMsg}>
                ¿Seguro que deseas eliminar <strong>"{modalDel.nombre}"</strong>?<br />
                Los productos asociados quedarán sin categoría.
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