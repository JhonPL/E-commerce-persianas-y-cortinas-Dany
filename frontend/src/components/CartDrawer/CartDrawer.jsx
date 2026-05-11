import { useEffect, useState } from 'react'
import { X, Trash2, ShoppingBag, Plus, Minus } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useCart } from '../../context/CartContext'
import styles from './CartDrawer.module.css'

const formatCOP = (n) =>
  new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(n)

export default function CartDrawer() {
  const { items, total, count, isOpen, closeCart, removeItem, updateCantidad } = useCart()
  const [imageErrors, setImageErrors] = useState({})

  // Bloquear scroll cuando está abierto
  useEffect(() => {
    document.body.style.overflow = isOpen ? 'hidden' : ''
    return () => { document.body.style.overflow = '' }
  }, [isOpen])

  // Cerrar con Escape
  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') closeCart() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [closeCart])

  return (
    <>
      {/* Backdrop */}
      <div
        className={`${styles.backdrop} ${isOpen ? styles.backdropVisible : ''}`}
        onClick={closeCart}
        aria-hidden="true"
      />

      {/* Drawer */}
      <aside className={`${styles.drawer} ${isOpen ? styles.drawerOpen : ''}`} role="dialog" aria-label="Carrito de compras">
        {/* Header */}
        <div className={styles.header}>
          <div className={styles.headerTitle}>
            <ShoppingBag size={18} />
            <span>Carrito</span>
            {count > 0 && <span className={styles.headerCount}>{count}</span>}
          </div>
          <button className={styles.closeBtn} onClick={closeCart} aria-label="Cerrar carrito">
            <X size={20} />
          </button>
        </div>

        {/* Items */}
        <div className={styles.body}>
          {items.length === 0 ? (
            <div className={styles.empty}>
              <ShoppingBag size={40} strokeWidth={1} />
              <p>Tu carrito está vacío</p>
              <Link to="/tienda" onClick={closeCart} className={styles.emptyLink}>
                Explorar productos →
              </Link>
            </div>
          ) : (
            <ul className={styles.list}>
              {items.map((item) => {
                const imgKey = item.key
                const imgSrc = imageErrors[imgKey]
                  ? 'https://images.unsplash.com/photo-1585128903994-9788298ef4fd?w=120&q=75'
                  : (item.product.imagen_principal || 'https://images.unsplash.com/photo-1585128903994-9788298ef4fd?w=120&q=75')

                return (
                  <li key={item.key} className={styles.item}>
                    <img
                      src={imgSrc}
                      alt={item.product.nombre}
                      className={styles.itemImg}
                      onError={() => setImageErrors(prev => ({ ...prev, [imgKey]: true }))}
                    />
                    <div className={styles.itemInfo}>
                      <span className={styles.itemNombre}>{item.product.nombre}</span>
                      <span className={styles.itemMedidas}>
                        {item.ancho} × {item.alto} cm — {item.area.toFixed(2)} m²
                      </span>
                      <span className={styles.itemPrecio}>{formatCOP(item.precioTotal)}</span>
                      <div className={styles.itemCantidad}>
                        <button
                          className={styles.cantidadBtn}
                          onClick={() => updateCantidad(item.key, item.cantidad - 1)}
                          aria-label="Disminuir cantidad"
                          title="Disminuir"
                        >
                          <Minus size={14} />
                        </button>
                        <span className={styles.cantidadValue}>{item.cantidad}</span>
                        <button
                          className={styles.cantidadBtn}
                          onClick={() => updateCantidad(item.key, item.cantidad + 1)}
                          aria-label="Aumentar cantidad"
                          title="Aumentar"
                        >
                          <Plus size={14} />
                        </button>
                      </div>
                    </div>
                    <button
                      className={styles.removeBtn}
                      onClick={() => removeItem(item.key)}
                      aria-label={`Eliminar ${item.product.nombre}`}
                    >
                      <Trash2 size={14} />
                    </button>
                  </li>
                )
              })}
            </ul>
          )}
        </div>

        {/* Footer con total y CTA */}
        {items.length > 0 && (
          <div className={styles.footer}>
            <div className={styles.totalRow}>
              <span className={styles.totalLabel}>Total</span>
              <span className={styles.totalValue}>{formatCOP(total)}</span>
            </div>
            <p className={styles.totalNote}>* Precio calculado según medidas ingresadas</p>
            <Link to="/checkout" onClick={closeCart} className={styles.checkoutBtn}>
              Proceder al pago
            </Link>
          </div>
        )}
      </aside>
    </>
  )
}