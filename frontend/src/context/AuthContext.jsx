import { createContext, useContext, useReducer, useCallback } from 'react'

// URL base del backend
const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1'

// Convierte los errores de DRF (pueden ser objeto o string) a un mensaje legible
function extraerError(data) {
  if (!data) return 'Error desconocido'
  if (typeof data === 'string') return data
  if (data.detail) return data.detail
  // DRF devuelve { campo: ["mensaje"], ... }
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

  // ── Login local ───────────────────────────────────────────────────
  const login = useCallback(async (email, password) => {
    dispatch({ type: 'AUTH_START' })
    try {
      // TODO: reemplazar mock por fetch real cuando el backend esté listo
      // Mock temporal para desarrollo
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

  // ── Registro real contra el backend ──────────────────────────────
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
        // DRF devuelve errores como { campo: ["mensaje"] } o { detail: "..." }
        throw new Error(extraerError(data))
      }

      // Registro exitoso → login automático para obtener el token JWT
      const loginResult = await fetch(`${API_URL}/auth/login/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })

      const loginData = await loginResult.json()

      if (!loginResult.ok) {
        throw new Error(extraerError(loginData))
      }

      // loginData = { usuario: { usuario_id, nombre, email, rol_nombre }, access, refresh }
      const user = {
        usuario_id: loginData.usuario.usuario_id,
        nombre:     loginData.usuario.nombre,
        email:      loginData.usuario.email,
        rol:        loginData.usuario.rol_nombre,
      }

      dispatch({ type: 'AUTH_SUCCESS', payload: { user, token: loginData.access } })
      return { success: true, rol: user.rol }

    } catch (err) {
      dispatch({ type: 'AUTH_ERROR', payload: err.message })
      return { success: false, error: err.message }
    }
  }, [])

  const logout     = useCallback(() => dispatch({ type: 'LOGOUT' }), [])
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