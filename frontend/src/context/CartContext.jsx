// frontend/src/context/CartContext.jsx
import { createContext, useContext, useReducer, useCallback, useEffect } from 'react'
import { useAuth } from './AuthContext'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1'

// ─── Estado inicial ───────────────────────────────────────────────────────────
const initialState = {
  items:  [],    // [{ key, item_id?, product, ancho, alto, area, precioTotal, cantidad }]
  isOpen: false,
  synced: false, // evita sincronizar más de una vez por sesión
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
function calcItem(product, ancho, alto, cantidad = 1) {
  const area       = (parseFloat(ancho) * parseFloat(alto)) / 10000
  const precioUnit = parseFloat(area.toFixed(4)) * parseFloat(product.precio_m2)
  return {
    area:       parseFloat(area.toFixed(4)),
    precioTotal: parseFloat((precioUnit * cantidad).toFixed(2)),
  }
}

function makeKey(producto_id, ancho, alto) {
  return `${producto_id}-${ancho}-${alto}`
}

/** Extrae imagen_principal de varias posibles estructuras de producto */
function extractImagenPrincipal(product) {
  return (
    product.imagen_principal ||  // URL directa del backend
    product.imagenes?.[0]?.url || // Array de imágenes (como viene desde Detalle.jsx)
    null
  )
}

/** Convierte un ítem del backend al formato interno del CartContext */
function backendItemToLocal(item) {
  const product = {
    producto_id:      item.producto_id ?? item.producto,
    nombre:           item.nombre ?? item.producto_detalle?.nombre,
    precio_m2:        item.precio_m2 ?? item.producto_detalle?.precio_m2,
    imagen_principal: item.imagen_principal ?? item.producto_detalle?.imagen_principal,
  }
  const ancho = parseFloat(item.ancho_cm)
  const alto  = parseFloat(item.alto_cm)
  return {
    key:         makeKey(product.producto_id, ancho, alto),
    item_id:     item.item_id,
    product,
    ancho,
    alto,
    area:        parseFloat(item.area_m2),
    precioTotal: parseFloat(item.subtotal ?? 0),
    cantidad:    item.cantidad,
  }
}

// ─── Reducer ──────────────────────────────────────────────────────────────────
function cartReducer(state, action) {
  switch (action.type) {

    case 'LOAD_FROM_BACKEND':
      return {
        ...state,
        items: Array.isArray(action.payload) ? action.payload.map(backendItemToLocal) : [],
        synced: true,
      }

    case 'ADD_ITEM': {
      const { product, ancho, alto } = action.payload
      const key    = makeKey(product.producto_id, ancho, alto)
      const exists = state.items.find(i => i.key === key)
      // Normalizar producto: asegurar que imagen_principal es una URL string
      const normalizedProduct = {
        ...product,
        imagen_principal: extractImagenPrincipal(product),
      }
      if (exists) {
        const cantidad = exists.cantidad + 1
        return {
          ...state,
          items: state.items.map(i =>
            i.key === key
              ? { ...i, cantidad, precioTotal: calcItem(normalizedProduct, ancho, alto, cantidad).precioTotal }
              : i
          ),
        }
      }
      const calc = calcItem(normalizedProduct, ancho, alto, 1)
      return {
        ...state,
        items: [...state.items, { key, item_id: null, product: normalizedProduct, ancho, alto, ...calc, cantidad: 1 }],
      }
    }

    case 'REMOVE_ITEM':
      return { ...state, items: state.items.filter(i => i.key !== action.payload) }

    case 'UPDATE_CANTIDAD': {
      const { key, cantidad } = action.payload
      if (cantidad <= 0) return { ...state, items: state.items.filter(i => i.key !== key) }
      return {
        ...state,
        items: state.items.map(i => {
          if (i.key !== key) return i
          const calc = calcItem(i.product, i.ancho, i.alto, cantidad)
          return { ...i, cantidad, precioTotal: calc.precioTotal }
        }),
      }
    }

    // Para compatibilidad con Detalle.jsx que llama updateMedidas
    case 'UPDATE_MEDIDAS': {
      const { key, ancho, alto, product } = action.payload
      const newKey = makeKey(product.producto_id, ancho, alto)
      const normalizedProduct = {
        ...product,
        imagen_principal: extractImagenPrincipal(product),
      }
      const calc   = calcItem(normalizedProduct, ancho, alto, 1)
      return {
        ...state,
        items: state.items.map(i =>
          i.key === key ? { ...i, key: newKey, product: normalizedProduct, ancho, alto, ...calc } : i
        ),
      }
    }

    case 'SET_ITEM_ID': {
      const { key, item_id } = action.payload
      return { ...state, items: state.items.map(i => i.key === key ? { ...i, item_id } : i) }
    }

    case 'TOGGLE_CART': return { ...state, isOpen: !state.isOpen }
    case 'CLOSE_CART':  return { ...state, isOpen: false }
    case 'CLEAR_CART':  return { ...initialState }

    default: return state
  }
}

// ─── Context ──────────────────────────────────────────────────────────────────
const CartContext = createContext(null)

export function CartProvider({ children }) {
  const [state, dispatch] = useReducer(cartReducer, initialState)
  const { user, token }   = useAuth()

  // ── Al hacer login: sincronizar carrito local → backend y cargar el resultado
  useEffect(() => {
    if (!user || !token || state.synced) return

    const sincronizar = async () => {
      try {
        // Convertir ítems locales al formato que espera el backend
        const itemsLocales = state.items.map(i => ({
          producto:  i.product.producto_id,
          ancho_cm:  i.ancho,
          alto_cm:   i.alto,
          cantidad:  i.cantidad,
        }))

        const res = await fetch(`${API_URL}/carrito/sincronizar/`, {
          method:  'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
          body:    JSON.stringify({ items: itemsLocales }),
        })
        if (!res.ok) throw new Error('Sync failed')
        const data = await res.json()
        if (Array.isArray(data?.items)) {
          dispatch({ type: 'LOAD_FROM_BACKEND', payload: data.items })
        }
      } catch {
        // Si falla la sync, cargar igualmente el carrito guardado en BD
        try {
          const res  = await fetch(`${API_URL}/carrito/`, {
            headers: { Authorization: `Bearer ${token}` },
          })
          if (res.ok) {
            const data = await res.json()
            if (Array.isArray(data?.items)) {
              dispatch({ type: 'LOAD_FROM_BACKEND', payload: data.items })
            }
          }
        } catch { /* fallo silencioso */ }
      }
    }
    sincronizar()
  }, [user, token]) // eslint-disable-line react-hooks/exhaustive-deps

  // ── Al hacer logout: limpiar carrito
  useEffect(() => {
    if (!user) dispatch({ type: 'CLEAR_CART' })
  }, [user])

  // ── Acciones ───────────────────────────────────────────────────────────────

  const addItem = useCallback(async (product, ancho, alto) => {
    // 1. Actualizar estado local inmediatamente
    dispatch({ type: 'ADD_ITEM', payload: { product, ancho, alto } })

    if (!token) return  // sin sesión → solo local

    // 2. Persistir en backend
    try {
      const res = await fetch(`${API_URL}/carrito/`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body:    JSON.stringify({
          producto: product.producto_id,
          ancho_cm: ancho,
          alto_cm:  alto,
          cantidad: 1,
        }),
      })
      if (!res.ok) return
      const data = await res.json()
      // Actualizar item_ids desde la respuesta del backend
      if (Array.isArray(data?.items)) {
        dispatch({ type: 'LOAD_FROM_BACKEND', payload: data.items })
      }
    } catch { /* fallo silencioso */ }
  }, [token])

  const removeItem = useCallback(async (key) => {
    const item = state.items.find(i => i.key === key)
    dispatch({ type: 'REMOVE_ITEM', payload: key })

    if (!token || !item?.item_id) return
    try {
      await fetch(`${API_URL}/carrito/${item.item_id}/`, {
        method:  'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      })
    } catch { /* fallo silencioso */ }
  }, [token, state.items])

  const updateCantidad = useCallback(async (key, cantidad) => {
    const item = state.items.find(i => i.key === key)
    dispatch({ type: 'UPDATE_CANTIDAD', payload: { key, cantidad } })

    if (!token || !item?.item_id) return
    try {
      await fetch(`${API_URL}/carrito/${item.item_id}/`, {
        method:  'PATCH',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body:    JSON.stringify({ cantidad }),
      })
    } catch { /* fallo silencioso */ }
  }, [token, state.items])

  // Compatibilidad con Detalle.jsx
  const updateMedidas = useCallback((key, ancho, alto, product) => {
    dispatch({ type: 'UPDATE_MEDIDAS', payload: { key, ancho, alto, product } })
  }, [])

  const clearCart = useCallback(async () => {
    dispatch({ type: 'CLEAR_CART' })
    if (!token) return
    try {
      await fetch(`${API_URL}/carrito/limpiar/`, {
        method:  'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      })
    } catch { /* fallo silencioso */ }
  }, [token])

  const toggleCart = useCallback(() => dispatch({ type: 'TOGGLE_CART' }), [])
  const closeCart  = useCallback(() => dispatch({ type: 'CLOSE_CART' }), [])

  const total = state.items.reduce((sum, i) => sum + i.precioTotal, 0)
  const count = state.items.reduce((sum, i) => sum + i.cantidad, 0)

  return (
    <CartContext.Provider value={{
      ...state, total, count,
      addItem, removeItem, updateCantidad, updateMedidas,
      toggleCart, closeCart, clearCart,
    }}>
      {children}
    </CartContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export const useCart = () => {
  const ctx = useContext(CartContext)
  if (!ctx) throw new Error('useCart debe usarse dentro de CartProvider')
  return ctx
}