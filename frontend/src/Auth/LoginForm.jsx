import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Eye, EyeOff, Mail, Lock, AlertCircle } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import styles from './Auth.module.css'

const GoogleIcon = () => (
  <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
    <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844a4.14 4.14 0 01-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615z" fill="#4285F4"/>
    <path d="M9 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 009 18z" fill="#34A853"/>
    <path d="M3.964 10.706A5.41 5.41 0 013.682 9c0-.593.102-1.17.282-1.706V4.962H.957A8.996 8.996 0 000 9c0 1.452.348 2.827.957 4.038l3.007-2.332z" fill="#FBBC05"/>
    <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 00.957 4.962L3.964 7.294C4.672 5.163 6.656 3.58 9 3.58z" fill="#EA4335"/>
  </svg>
)

export default function LoginForm({ from, onSwitchToRegister }) {
  const navigate = useNavigate()
  const { login, loading, error, clearError } = useAuth()

  const [email,       setEmail]       = useState('')
  const [password,    setPassword]    = useState('')
  const [showPass,    setShowPass]    = useState(false)
  const [remember,    setRemember]    = useState(false)
  const [fieldErrors, setFieldErrors] = useState({})

  const validate = () => {
    const errs = {}
    if (!email.trim())               errs.email    = 'Ingresa tu correo'
    else if (!/\S+@\S+\.\S+/.test(email)) errs.email = 'Correo inválido'
    if (!password)                   errs.password = 'Ingresa tu contraseña'
    setFieldErrors(errs)
    return Object.keys(errs).length === 0
  }

  const handleSubmit = async () => {
    clearError()
    if (!validate()) return
    const result = await login(email, password)
    if (result.success) {
      navigate(result.rol === 'admin' ? '/admin' : from, { replace: true })
    }
  }

  const handleGoogleLogin = () => {
    // TODO: redirigir a /api/auth/google (OAuth flow)
    alert('Google OAuth — conectar con el backend')
  }

  return (
    <div className={styles.formBody}>
      <div className={styles.formHeader}>
        <h1 className={styles.formTitle}>Ingresar</h1>
        <p className={styles.formSub}>Ingresa tu correo y contraseña para continuar</p>
      </div>

      {/* OAuth */}
      <div className={styles.oauthRow}>
        <button className={styles.oauthBtn} onClick={handleGoogleLogin} type="button">
          <GoogleIcon />
          Ingresar con Google
        </button>
      </div>

      {/* Divisor */}
      <div className={styles.divider}>
        <span className={styles.dividerLine} />
        <span className={styles.dividerText}>O</span>
        <span className={styles.dividerLine} />
      </div>

      {/* Error global */}
      {error && (
        <div className={styles.alertError}>
          <AlertCircle size={15} />
          <span>{error}</span>
        </div>
      )}

      {/* Email */}
      <div className={styles.field}>
        <label className={styles.label}>
          Correo electrónico <span className={styles.required}>*</span>
        </label>
        <div className={styles.inputWrapper}>
          <Mail size={16} className={styles.inputIcon} />
          <input
            type="email"
            placeholder="info@correo.com"
            value={email}
            onChange={e => { setEmail(e.target.value); setFieldErrors(p => ({ ...p, email: '' })) }}
            className={`${styles.input} ${fieldErrors.email ? styles.inputErr : ''}`}
            autoComplete="email"
          />
        </div>
        {fieldErrors.email && <span className={styles.fieldError}>{fieldErrors.email}</span>}
      </div>

      {/* Password */}
      <div className={styles.field}>
        <label className={styles.label}>
          Contraseña <span className={styles.required}>*</span>
        </label>
        <div className={styles.inputWrapper}>
          <Lock size={16} className={styles.inputIcon} />
          <input
            type={showPass ? 'text' : 'password'}
            placeholder="Ingresa tu contraseña"
            value={password}
            onChange={e => { setPassword(e.target.value); setFieldErrors(p => ({ ...p, password: '' })) }}
            className={`${styles.input} ${styles.inputPad} ${fieldErrors.password ? styles.inputErr : ''}`}
            autoComplete="current-password"
          />
          <button
            type="button"
            className={styles.eyeBtn}
            onClick={() => setShowPass(v => !v)}
            aria-label={showPass ? 'Ocultar contraseña' : 'Mostrar contraseña'}
          >
            {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        </div>
        {fieldErrors.password && <span className={styles.fieldError}>{fieldErrors.password}</span>}
      </div>

      {/* Remember + Forgot */}
      <div className={styles.rowBetween}>
        <label className={styles.checkLabel}>
          <input
            type="checkbox"
            checked={remember}
            onChange={e => setRemember(e.target.checked)}
            className={styles.checkbox}
          />
          Mantener sesión
        </label>
        <button type="button" className={styles.linkBtn}>
          ¿Olvidaste tu contraseña?
        </button>
      </div>

      {/* Submit */}
      <button
        type="button"
        className={`${styles.submitBtn} ${loading ? styles.submitLoading : ''}`}
        onClick={handleSubmit}
        disabled={loading}
      >
        {loading ? <span className={styles.spinner} /> : 'Ingresar'}
      </button>

      {/* Switch */}
      <p className={styles.switchText}>
        ¿No tienes cuenta?{' '}
        <button type="button" className={styles.switchLink} onClick={onSwitchToRegister}>
          Regístrate
        </button>
      </p>
    </div>
  )
}