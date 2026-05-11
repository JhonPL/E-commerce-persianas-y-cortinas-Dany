import api from './axios'

export const registroAPI = async (datos) => {
  const response = await api.post('/auth/registro/', datos)
  return response.data
}

export const loginAPI = async (email, password) => {
  const response = await api.post('/auth/login/', { email, password })
  const { access, refresh, usuario } = response.data

  // Guardar en localStorage (persiste aunque cierres el navegador)
  localStorage.setItem('access_token',  access)
  localStorage.setItem('refresh_token', refresh)
  localStorage.setItem('usuario',       JSON.stringify(usuario))

  return { access, refresh, usuario }
}

export const logoutAPI = () => {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('usuario')
}

export const miPerfilAPI = async () => {
  const response = await api.get('/auth/me/')
  return response.data
}
