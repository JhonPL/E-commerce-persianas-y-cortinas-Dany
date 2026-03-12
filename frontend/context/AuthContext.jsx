import { createContext, useContext, useReducer, useCallback } from 'react'

const initialState = {
  user: null,       // { usuario_id, nombre, email, rol }
  token: null,
  loading: false,
  error: null,
}

function authReducer(state, action) {
  switch (action.type) {
    case 'AUTH_START':
      return { ...state, loading: true, error: null }
    case 'AUTH_SUCCESS':
      return { ...state, loading: false, user: action.payload.user, token: action.payload.token, error: null }
    case 'AUTH_ERROR':
      return { ...state, loading: false, error: action.payload }
    case 'LOGOUT':
      return { ...initialState }
    default:
      return state
  }
}

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [state, dispatch] = useReducer(authReducer, initialState)

  // Login local (email + password)
  const login = useCallback(async (email, password) => {
    dispatch({ type: 'AUTH_START' })
    try {
      // TODO: reemplazar por fetch real a /api/auth/login
      // Simulación para desarrollo frontend
      await new Promise(r => setTimeout(r, 800))
      if (email === 'admin@cortinasydany.com' && password === 'Admin2024$') {
        const user = { usuario_id: 1, nombre: 'Administrador Dany', email, rol: 'admin' }
        dispatch({ type: 'AUTH_SUCCESS', payload: { user, token: 'mock-token-admin' } })
        return { success: true, rol: 'admin' }
      }
      if (password === 'Cliente123$') {
        const user = { usuario_id: 2, nombre: email.split('@')[0], email, rol: 'cliente' }
        dispatch({ type: 'AUTH_SUCCESS', payload: { user, token: 'mock-token-cliente' } })
        return { success: true, rol: 'cliente' }
      }
      throw new Error('Correo o contraseña incorrectos')
    } catch (err) {
      dispatch({ type: 'AUTH_ERROR', payload: err.message })
      return { success: false, error: err.message }
    }
  }, [])

  // Registro local
  const register = useCallback(async (nombre, email, password) => {
    dispatch({ type: 'AUTH_START' })
    try {
      await new Promise(r => setTimeout(r, 800))
      // TODO: reemplazar por fetch real a /api/auth/register
      const user = { usuario_id: Date.now(), nombre, email, rol: 'cliente' }
      dispatch({ type: 'AUTH_SUCCESS', payload: { user, token: 'mock-token-new' } })
      return { success: true }
    } catch (err) {
      dispatch({ type: 'AUTH_ERROR', payload: err.message })
      return { success: false, error: err.message }
    }
  }, [])

  const logout = useCallback(() => dispatch({ type: 'LOGOUT' }), [])
  const clearError = useCallback(() => dispatch({ type: 'AUTH_ERROR', payload: null }), [])

  return (
    <AuthContext.Provider value={{ ...state, login, register, logout, clearError }}>
      {children}
    </AuthContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth debe usarse dentro de AuthProvider')
  return ctx
}