import { createContext, useContext, useReducer, useCallback, useEffect } from 'react'
import { loginAPI, registroAPI, logoutAPI } from '../api/auth'

const initialState = {
  user:    null,
  token:   null,
  loading: false,
  error:   null,
}

function authReducer(state, action) {
  switch (action.type) {
    case 'AUTH_START':
      return { ...state, loading: true, error: null }

    case 'AUTH_SUCCESS':
      return {
        ...state,
        loading: false,
        user:    action.payload.user,
        token:   action.payload.token,
        error:   null
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

  // ─────────────────────────────────────────────────
  // NUEVO: Al abrir la app, recuperar sesión guardada
  // Si el usuario ya había iniciado sesión antes
  // (cerró el navegador y volvió), recuperamos su sesión
  // del localStorage automáticamente
  // ─────────────────────────────────────────────────
  useEffect(() => {
    const usuarioGuardado = localStorage.getItem('usuario')
    const tokenGuardado   = localStorage.getItem('access_token')

    if (usuarioGuardado && tokenGuardado) {
      dispatch({
        type: 'AUTH_SUCCESS',
        payload: {
          user:  JSON.parse(usuarioGuardado),
          token: tokenGuardado
        }
      })
    }
  }, [])

  // ─────────────────────────────────────────────────
  // LOGIN — reemplaza la simulación por llamada real
  //
  // ANTES: esperaba 800ms y chequeaba emails hardcodeados
  // AHORA: llama al backend real y maneja la respuesta
  // ─────────────────────────────────────────────────
  const login = useCallback(async (email, password) => {
    dispatch({ type: 'AUTH_START' })
    try {
      // Llamada real al backend Django
      const { usuario, access } = await loginAPI(email, password)

      // El reducer guarda user y token en el estado global
      dispatch({
        type: 'AUTH_SUCCESS',
        payload: {
          user:  usuario,   // { usuario_id, nombre, email, rol_nombre, ... }
          token: access     // "eyJhbGciOiJIUzI1NiJ9..."
        }
      })

      return {
        success: true,
        rol:     usuario.rol_nombre  // 'admin' o 'cliente'
      }

    } catch (err) {
      // Capturar mensaje de error del backend
      // El backend devuelve errores en diferentes formatos:
      const mensaje =
        err.response?.data?.non_field_errors?.[0] || // error de validación
        err.response?.data?.detail               ||  // error de autenticación
        err.response?.data?.email?.[0]           ||  // error de campo email
        'Correo o contraseña incorrectos'            // mensaje por defecto

      dispatch({ type: 'AUTH_ERROR', payload: mensaje })
      return { success: false, error: mensaje }
    }
  }, [])

  // ─────────────────────────────────────────────────
  // REGISTRO — reemplaza la simulación por llamada real
  //
  // ANTES: creaba un usuario falso con Date.now()
  // AHORA: llama al backend y crea el usuario en PostgreSQL
  // ─────────────────────────────────────────────────
  const register = useCallback(async (nombre, email, password) => {
    dispatch({ type: 'AUTH_START' })
    try {
      // Llamada real al backend Django
      // El backend crea el usuario Y su perfil cliente automáticamente
      await registroAPI({
        nombre,
        email,
        password,
        password_confirmar: password
      })

      // Después del registro → hacer login automáticamente
      // Para que el usuario no tenga que volver a escribir sus datos
      const resultado = await login(email, password)
      return resultado

    } catch (err) {
      const mensaje =
        err.response?.data?.email?.[0]    ||  // "Ya existe una cuenta con este email"
        err.response?.data?.password?.[0] ||  // "La contraseña debe tener 8 caracteres"
        err.response?.data?.nombre?.[0]   ||  // error en nombre
        'Error al crear la cuenta'

      dispatch({ type: 'AUTH_ERROR', payload: mensaje })
      return { success: false, error: mensaje }
    }
  }, [login])

  const logout = useCallback(() => {
    // Borrar tokens del localStorage
    logoutAPI()
    // Limpiar el estado global
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
      esAdmin:      state.user?.rol_nombre === 'admin',
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