import { createContext, useContext, useReducer, useCallback, useEffect, useRef } from 'react'
import { API_URL } from '../config/api'

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
  refreshToken: null,
  loading: false,
  error: null,
}

const initialAuthState = () => {
  const token = localStorage.getItem('token')
  const refreshToken = localStorage.getItem('refresh_token')
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
  return { ...initialState, user, token, refreshToken }
}

function authReducer(state, action) {
  switch (action.type) {
    case 'AUTH_START':
      return { ...state, loading: true, error: null }
    case 'AUTH_SUCCESS':
      sessionStorage.setItem('token', action.payload.token)
      localStorage.setItem('token', action.payload.token)
      if (action.payload.refreshToken) {
        localStorage.setItem('refresh_token', action.payload.refreshToken)
      } else {
        localStorage.removeItem('refresh_token')
      }
      localStorage.setItem('user', JSON.stringify(action.payload.user))
      return {
        ...state,
        loading: false,
        user: action.payload.user,
        token: action.payload.token,
        refreshToken: action.payload.refreshToken || null,
        error: null,
      }
    case 'AUTH_ERROR':
      return { ...state, loading: false, error: action.payload }
    case 'LOGOUT':
      sessionStorage.removeItem('token')
      localStorage.removeItem('token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
      localStorage.removeItem('access_token')
      localStorage.removeItem('usuario')
      return { ...initialState }
    case 'RESTORE':
      return {
        ...state,
        user: action.payload.user,
        token: action.payload.token,
        refreshToken: action.payload.refreshToken,
      }
    case 'TOKEN_REFRESH':
      sessionStorage.setItem('token', action.payload.token)
      localStorage.setItem('token', action.payload.token)
      if (action.payload.refreshToken) {
        localStorage.setItem('refresh_token', action.payload.refreshToken)
      }
      return {
        ...state,
        token: action.payload.token,
        refreshToken: action.payload.refreshToken || state.refreshToken,
      }
    default:
      return state
  }
}

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [state, dispatch] = useReducer(authReducer, undefined, initialAuthState)
  const refreshPromise = useRef(null)

  // ── Restaurar sesión desde localStorage al cargar ──────────────────
  useEffect(() => {
    const token = localStorage.getItem('token')
    const userJSON = localStorage.getItem('user')
    if (token && userJSON) {
      try {
        const user = JSON.parse(userJSON)
        dispatch({
          type: 'RESTORE',
          payload: { token, user, refreshToken: localStorage.getItem('refresh_token') },
        })
      } catch {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
      }
    }
  }, [])

  const refreshAccessToken = useCallback(async () => {
    if (refreshPromise.current) return refreshPromise.current

    const refreshToken = localStorage.getItem('refresh_token')
    if (!refreshToken) {
      dispatch({ type: 'LOGOUT' })
      return null
    }

    refreshPromise.current = (async () => {
      try {
        const response = await fetch(`${API_URL}/auth/token/refresh/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh: refreshToken }),
        })
        const data = await response.json().catch(() => ({}))
        if (!response.ok || !data.access) {
          dispatch({ type: 'LOGOUT' })
          return null
        }

        const nextRefreshToken = data.refresh || refreshToken
        dispatch({
          type: 'TOKEN_REFRESH',
          payload: { token: data.access, refreshToken: nextRefreshToken },
        })
        return data.access
      } finally {
        refreshPromise.current = null
      }
    })()

    return refreshPromise.current
  }, [])

  const authenticatedFetch = useCallback(async (url, options = {}) => {
    const request = (accessToken) => {
      const headers = new Headers(options.headers || {})
      if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`)
      return fetch(url, { ...options, headers })
    }

    const response = await request(localStorage.getItem('token'))
    if (response.status !== 401) return response

    const refreshedToken = await refreshAccessToken()
    return refreshedToken ? request(refreshedToken) : response
  }, [refreshAccessToken])

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

      dispatch({
        type: 'AUTH_SUCCESS',
        payload: { user, token: data.access, refreshToken: data.refresh },
      })
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
  const googleAuth = useCallback(async (credential) => {
    dispatch({ type: 'AUTH_START' })
    try {
      const res = await fetch(`${API_URL}/auth/google/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ credential }),
      })

      const data = await res.json()

      if (!res.ok) {
        throw new Error(extraerError(data))
      }

      const user = {
        usuario_id: data.usuario.usuario_id,
        nombre:     data.usuario.nombre,
        email:      data.usuario.email,
        rol:        data.usuario.rol_nombre,
      }

      dispatch({
        type: 'AUTH_SUCCESS',
        payload: { user, token: data.access, refreshToken: data.refresh },
      })
      return { success: true, rol: user.rol }

    } catch (err) {
      dispatch({ type: 'AUTH_ERROR', payload: err.message })
      return { success: false, error: err.message }
    }
  }, [])
  const googleExchange = useCallback(async (code, redirectUri) => {
    dispatch({ type: 'AUTH_START' })
    try {
      const res = await fetch(`${API_URL}/auth/google/exchange/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, redirect_uri: redirectUri }),
      })

      const data = await res.json()

      if (!res.ok) {
        throw new Error(extraerError(data))
      }

      const user = {
        usuario_id: data.usuario.usuario_id,
        nombre:     data.usuario.nombre,
        email:      data.usuario.email,
        rol:        data.usuario.rol_nombre,
      }

      dispatch({
        type: 'AUTH_SUCCESS',
        payload: { user, token: data.access, refreshToken: data.refresh },
      })
      return { success: true, rol: user.rol }

    } catch (err) {
      dispatch({ type: 'AUTH_ERROR', payload: err.message })
      return { success: false, error: err.message }
    }
  }, [])

  const logout     = useCallback(() => {
    dispatch({ type: 'LOGOUT' })
    window.location.href = '/'
  }, [])
  const clearError = useCallback(() => dispatch({ type: 'AUTH_ERROR', payload: null }), [])

  return (
    <AuthContext.Provider value={{
      ...state,
      login,
      register,
      googleAuth,
      googleExchange,
      logout,
      clearError,
      authenticatedFetch,
    }}>
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
