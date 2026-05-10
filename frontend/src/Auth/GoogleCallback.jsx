import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function GoogleCallback() {
  const navigate = useNavigate()
  const { googleExchange } = useAuth()
  const [message, setMessage] = useState('Procesando login con Google...')

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const code = params.get('code')
    const state = params.get('state')
    const error = params.get('error')

    const expectedState = sessionStorage.getItem('google_oauth_state')
    const from = sessionStorage.getItem('oauth_from') || '/'
    const redirectUri = `${window.location.origin}/oauth/google`

    async function run() {
      if (error) {
        setMessage('Google canceló o bloqueó el inicio de sesión.')
        navigate('/login', { replace: true })
        return
      }
      if (!code) {
        setMessage('No llegó el código de Google.')
        navigate('/login', { replace: true })
        return
      }
      if (!state || !expectedState || state !== expectedState) {
        setMessage('Estado inválido. Intenta nuevamente.')
        navigate('/login', { replace: true })
        return
      }

      sessionStorage.removeItem('google_oauth_state')
      sessionStorage.removeItem('oauth_from')

      const result = await googleExchange(code, redirectUri)
      if (!result.success) {
        setMessage(result.error || 'No se pudo iniciar sesión con Google.')
        navigate('/login', { replace: true })
        return
      }

      navigate(result.rol === 'admin' ? '/admin' : from, { replace: true })
    }

    run()
  }, [googleExchange, navigate])

  return (
    <div style={{ padding: 24, fontFamily: 'system-ui, -apple-system, Segoe UI, sans-serif' }}>
      <p>{message}</p>
    </div>
  )
}
