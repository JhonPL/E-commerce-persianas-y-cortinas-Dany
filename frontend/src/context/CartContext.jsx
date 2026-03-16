import { createContext, useContext, useReducer, useCallback } from 'react'

// ─── Estado inicial ───────────────────────────────────────────────────────────
const initialState = {
  items: [],       // { product, ancho, alto, area, precioTotal, cantidad }
  isOpen: false,
}

// ─── Reducer ──────────────────────────────────────────────────────────────────
function cartReducer(state, action) {
  switch (action.type) {
    case 'ADD_ITEM': {
      const { product, ancho, alto } = action.payload
      const area = (ancho * alto) / 10000
      const precioTotal = parseFloat((area * product.precio_m2).toFixed(2))
      const key = `${product.producto_id}-${ancho}-${alto}`

      const exists = state.items.find(i => i.key === key)
      if (exists) {
        return {
          ...state,
          items: state.items.map(i =>
            i.key === key ? { ...i, cantidad: i.cantidad + 1, precioTotal: parseFloat((precioTotal * (i.cantidad + 1)).toFixed(2)) } : i
          ),
        }
      }
      return {
        ...state,
        items: [...state.items, { key, product, ancho, alto, area: parseFloat(area.toFixed(4)), precioTotal, cantidad: 1 }],
      }
    }

    case 'REMOVE_ITEM':
      return { ...state, items: state.items.filter(i => i.key !== action.payload) }

    case 'UPDATE_MEDIDAS': {
      const { key, ancho, alto, product } = action.payload
      const area = (ancho * alto) / 10000
      const precioTotal = parseFloat((area * product.precio_m2).toFixed(2))
      const newKey = `${product.producto_id}-${ancho}-${alto}`
      return {
        ...state,
        items: state.items.map(i =>
          i.key === key ? { ...i, key: newKey, ancho, alto, area: parseFloat(area.toFixed(4)), precioTotal } : i
        ),
      }
    }

    case 'TOGGLE_CART':
      return { ...state, isOpen: !state.isOpen }

    case 'CLOSE_CART':
      return { ...state, isOpen: false }

    case 'CLEAR_CART':
      return { ...state, items: [] }

    default:
      return state
  }
}

// ─── Context ──────────────────────────────────────────────────────────────────
const CartContext = createContext(null)

export function CartProvider({ children }) {
  const [state, dispatch] = useReducer(cartReducer, initialState)

  const addItem      = useCallback((product, ancho, alto) => dispatch({ type: 'ADD_ITEM', payload: { product, ancho, alto } }), [])
  const removeItem   = useCallback((key) => dispatch({ type: 'REMOVE_ITEM', payload: key }), [])
  const updateMedidas = useCallback((key, ancho, alto, product) => dispatch({ type: 'UPDATE_MEDIDAS', payload: { key, ancho, alto, product } }), [])
  const toggleCart   = useCallback(() => dispatch({ type: 'TOGGLE_CART' }), [])
  const closeCart    = useCallback(() => dispatch({ type: 'CLOSE_CART' }), [])
  const clearCart    = useCallback(() => dispatch({ type: 'CLEAR_CART' }), [])

  const total = state.items.reduce((sum, i) => sum + i.precioTotal, 0)
  const count = state.items.reduce((sum, i) => sum + i.cantidad, 0)

  return (
    <CartContext.Provider value={{ ...state, total, count, addItem, removeItem, updateMedidas, toggleCart, closeCart, clearCart }}>
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