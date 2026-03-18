import { createContext, useContext, useReducer, useCallback, useEffect } from 'react'
import { loginAPI, registroAPI, logoutAPI } from '../api/auth'

// URL base del backend
const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1'

const initialState = {
  user: null,
  token: null,
  loading: false,
  error: null,
}

function authReducer(state, action) {
  switch (action.type) {
    case 'AUTH_START':
      return { ...state, loading: true, error: null }

    case 'AUTH_SUCCESS':
      return {
        ...state,
        loading: false,
        user: action.payload.user,
        token: action.payload.token,
        error: null
      }

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

  // ✅ Recuperar sesión
  useEffect(() => {
    const usuarioGuardado = localStorage.getItem('usuario')
    const tokenGuardado = localStorage.getItem('access_token')

    if (usuarioGuardado && tokenGuardado) {
      dispatch({
        type: 'AUTH_SUCCESS',
        payload: {
          user: JSON.parse(usuarioGuardado),
          token: tokenGuardado
        }
      })
    }
  }, [])

  // ✅ LOGIN REAL
  const login = useCallback(async (email, password) => {
    dispatch({ type: 'AUTH_START' })
    try {
      const { usuario, access } = await loginAPI(email, password)

      // guardar en localStorage
      localStorage.setItem('usuario', JSON.stringify(usuario))
      localStorage.setItem('access_token', access)

      dispatch({
        type: 'AUTH_SUCCESS',
        payload: {
          user: usuario,
          token: access
        }
      })

      return {
        success: true,
        rol: usuario.rol_nombre
      }

    } catch (err) {
      const mensaje =
        err.response?.data?.non_field_errors?.[0] ||
        err.response?.data?.detail ||
        err.response?.data?.email?.[0] ||
        'Correo o contraseña incorrectos'

      dispatch({ type: 'AUTH_ERROR', payload: mensaje })
      return { success: false, error: mensaje }
    }
  }, [])

  // ✅ REGISTRO REAL + LOGIN AUTOMÁTICO
  const register = useCallback(async (nombre, email, password) => {
    dispatch({ type: 'AUTH_START' })
    try {
      await registroAPI({
        nombre,
        email,
        password,
        password_confirmar: password
      })

      // login automático
      return await login(email, password)

    } catch (err) {
      const mensaje =
        err.response?.data?.email?.[0] ||
        err.response?.data?.password?.[0] ||
        err.response?.data?.nombre?.[0] ||
        'Error al crear la cuenta'

      dispatch({ type: 'AUTH_ERROR', payload: mensaje })
      return { success: false, error: mensaje }
    }
  }, [login])

  // ✅ LOGOUT LIMPIO
  const logout = useCallback(() => {
    logoutAPI()
    localStorage.removeItem('usuario')
    localStorage.removeItem('access_token')
    dispatch({ type: 'LOGOUT' })
  }, [])

  const clearError = useCallback(() =>
    dispatch({ type: 'AUTH_ERROR', payload: null }), [])

  return (
    <AuthContext.Provider value={{
      ...state,
      login,
      register,
      logout,
      clearError,
      estaLogueado: !!state.user,
      esAdmin: state.user?.rol_nombre === 'admin',
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth debe usarse dentro de AuthProvider')
  return ctx
}