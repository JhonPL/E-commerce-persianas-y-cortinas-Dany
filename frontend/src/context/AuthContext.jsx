import { createContext, useContext, useReducer, useCallback, useEffect } from 'react'

// URL base del backend — agregar al .env del frontend:
// VITE_API_URL=http://127.0.0.1:8000/api/v1
const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1'

// Convierte los errores de DRF a un mensaje legible
function extraerError(data) {
  if (!data) return 'Error desconocido'
  if (typeof data === 'string') return data
  if (data.detail) return data.detail
  const primer = Object.values(data)[0]
  if (Array.isArray(primer)) return primer[0]
  return JSON.stringify(data)
}

const initialState = {
  user: null,       // { usuario_id, nombre, email, rol }
  token: null,
  loading: false,
  error: null,
}

const initialAuthState = () => {
  const token = localStorage.getItem('token')
  const userJson = localStorage.getItem('user')
  let user = null
  if (token && userJson) {
    try {
      user = JSON.parse(userJson)
    } catch {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
  }
  return { ...initialState, user, token }
}

function authReducer(state, action) {
  switch (action.type) {
    case 'AUTH_START':
      return { ...state, loading: true, error: null }
    case 'AUTH_SUCCESS':
      sessionStorage.setItem('token', action.payload.token)
      localStorage.setItem('token', action.payload.token)
      localStorage.setItem('user', JSON.stringify(action.payload.user))
      return { ...state, loading: false, user: action.payload.user, token: action.payload.token, error: null }
    case 'AUTH_ERROR':
      return { ...state, loading: false, error: action.payload }
    case 'LOGOUT':
      sessionStorage.removeItem('token')
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      return { ...initialState }
    case 'RESTORE':
      return { ...state, user: action.payload.user, token: action.payload.token }
    default:
      return state
  }
}

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [state, dispatch] = useReducer(authReducer, undefined, initialAuthState)

  // ── Restaurar sesión desde localStorage al cargar ──────────────────
  useEffect(() => {
    const token = localStorage.getItem('token')
    const userJSON = localStorage.getItem('user')
    if (token && userJSON) {
      try {
        const user = JSON.parse(userJSON)
        dispatch({ type: 'RESTORE', payload: { token, user } })
      } catch {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
      }
    }
  }, [])

  // ── Login real ────────────────────────────────────────────────────
  const login = useCallback(async (email, password) => {
    dispatch({ type: 'AUTH_START' })
    try {
      const res = await fetch(`${API_URL}/auth/login/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })

      const data = await res.json()

      if (!res.ok) {
        throw new Error(extraerError(data))
      }

      // data = { usuario: { usuario_id, nombre, email, rol_nombre }, access, refresh }
      const user = {
        usuario_id: data.usuario.usuario_id,
        nombre:     data.usuario.nombre,
        email:      data.usuario.email,
        rol:        data.usuario.rol_nombre,
      }

      dispatch({ type: 'AUTH_SUCCESS', payload: { user, token: data.access } })
      return { success: true, rol: user.rol }

    } catch (err) {
      dispatch({ type: 'AUTH_ERROR', payload: err.message })
      return { success: false, error: err.message }
    }
  }, [])

  // ── Registro real ─────────────────────────────────────────────────
  const register = useCallback(async (nombre, email, password) => {
    dispatch({ type: 'AUTH_START' })
    try {
      const res = await fetch(`${API_URL}/auth/registro/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nombre,
          email,
          password,
          password_confirmar: password,
        }),
      })

      const data = await res.json()

      if (!res.ok) {
        throw new Error(extraerError(data))
      }

      // Registro exitoso → login automático para obtener el token
      return await login(email, password)

    } catch (err) {
      dispatch({ type: 'AUTH_ERROR', payload: err.message })
      return { success: false, error: err.message }
    }
  }, [login])

  const logout     = useCallback(() => {
    dispatch({ type: 'LOGOUT' })
    window.location.href = '/'
  }, [])
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