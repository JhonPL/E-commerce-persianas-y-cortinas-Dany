import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Eye, EyeOff, Mail, Lock, User, AlertCircle, CheckCircle } from 'lucide-react'
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

// Indicador de fortaleza de contraseña
function PasswordStrength({ password }) {
  const checks = [
    { label: 'Mínimo 8 caracteres', ok: password.length >= 8 },
    { label: 'Una mayúscula',        ok: /[A-Z]/.test(password) },
    { label: 'Un número',            ok: /[0-9]/.test(password) },
  ]
  if (!password) return null
  return (
    <div className={styles.strengthBox}>
      {checks.map(c => (
        <span key={c.label} className={`${styles.strengthItem} ${c.ok ? styles.strengthOk : styles.strengthNo}`}>
          {c.ok ? <CheckCircle size={11} /> : <AlertCircle size={11} />}
          {c.label}
        </span>
      ))}
    </div>
  )
}

export default function RegisterForm({ from, onSwitchToLogin }) {
  const navigate = useNavigate()
  const { register, loading, error, clearError } = useAuth()

  const [nombre,      setNombre]      = useState('')
  const [email,       setEmail]       = useState('')
  const [password,    setPassword]    = useState('')
  const [confirm,     setConfirm]     = useState('')
  const [showPass,    setShowPass]    = useState(false)
  const [showConf,    setShowConf]    = useState(false)
  const [terms,       setTerms]       = useState(false)
  const [fieldErrors, setFieldErrors] = useState({})

  const validate = () => {
    const errs = {}
    if (!nombre.trim())                   errs.nombre   = 'Ingresa tu nombre'
    if (!email.trim())                    errs.email    = 'Ingresa tu correo'
    else if (!/\S+@\S+\.\S+/.test(email)) errs.email    = 'Correo inválido'
    if (!password)                        errs.password = 'Ingresa una contraseña'
    else if (password.length < 8)         errs.password = 'Mínimo 8 caracteres'
    if (password !== confirm)             errs.confirm  = 'Las contraseñas no coinciden'
    if (!terms)                           errs.terms    = 'Debes aceptar los términos'
    setFieldErrors(errs)
    return Object.keys(errs).length === 0
  }

  const handleSubmit = async () => {
    clearError()
    if (!validate()) return
    const result = await register(nombre, email, password)
    if (result.success) navigate(from, { replace: true })
  }

  const handleGoogleRegister = () => {
    alert('Google OAuth — conectar con el backend')
  }

  return (
    <div className={styles.formBody}>
      <div className={styles.formHeader}>
        <h1 className={styles.formTitle}>Crear cuenta</h1>
        <p className={styles.formSub}>Ingresa tus datos para registrarte</p>
      </div>

      {/* OAuth */}
      <div className={styles.oauthRow}>
        <button className={styles.oauthBtn} onClick={handleGoogleRegister} type="button">
          <GoogleIcon />
          Registrarse con Google
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

      {/* Nombre */}
      <div className={styles.field}>
        <label className={styles.label}>
          Nombre completo <span className={styles.required}>*</span>
        </label>
        <div className={styles.inputWrapper}>
          <User size={16} className={styles.inputIcon} />
          <input
            type="text"
            placeholder="Tu nombre"
            value={nombre}
            onChange={e => { setNombre(e.target.value); setFieldErrors(p => ({ ...p, nombre: '' })) }}
            className={`${styles.input} ${fieldErrors.nombre ? styles.inputErr : ''}`}
            autoComplete="name"
          />
        </div>
        {fieldErrors.nombre && <span className={styles.fieldError}>{fieldErrors.nombre}</span>}
      </div>

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
            placeholder="Mínimo 8 caracteres"
            value={password}
            onChange={e => { setPassword(e.target.value); setFieldErrors(p => ({ ...p, password: '' })) }}
            className={`${styles.input} ${styles.inputPad} ${fieldErrors.password ? styles.inputErr : ''}`}
            autoComplete="new-password"
          />
          <button type="button" className={styles.eyeBtn} onClick={() => setShowPass(v => !v)}>
            {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        </div>
        {fieldErrors.password && <span className={styles.fieldError}>{fieldErrors.password}</span>}
        <PasswordStrength password={password} />
      </div>

      {/* Confirmar password */}
      <div className={styles.field}>
        <label className={styles.label}>
          Confirmar contraseña <span className={styles.required}>*</span>
        </label>
        <div className={styles.inputWrapper}>
          <Lock size={16} className={styles.inputIcon} />
          <input
            type={showConf ? 'text' : 'password'}
            placeholder="Repite tu contraseña"
            value={confirm}
            onChange={e => { setConfirm(e.target.value); setFieldErrors(p => ({ ...p, confirm: '' })) }}
            className={`${styles.input} ${styles.inputPad} ${fieldErrors.confirm ? styles.inputErr : ''}`}
            autoComplete="new-password"
          />
          <button type="button" className={styles.eyeBtn} onClick={() => setShowConf(v => !v)}>
            {showConf ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        </div>
        {fieldErrors.confirm && <span className={styles.fieldError}>{fieldErrors.confirm}</span>}
      </div>

      {/* Términos */}
      <div className={styles.field}>
        <label className={`${styles.checkLabel} ${fieldErrors.terms ? styles.checkLabelErr : ''}`}>
          <input
            type="checkbox"
            checked={terms}
            onChange={e => { setTerms(e.target.checked); setFieldErrors(p => ({ ...p, terms: '' })) }}
            className={styles.checkbox}
          />
          Al crear una cuenta acepto los{' '}
          <button type="button" className={styles.linkBtn}>Términos y Condiciones</button>
          {' '}y la{' '}
          <button type="button" className={styles.linkBtn}>Política de Privacidad</button>
        </label>
        {fieldErrors.terms && <span className={styles.fieldError}>{fieldErrors.terms}</span>}
      </div>

      {/* Submit */}
      <button
        type="button"
        className={`${styles.submitBtn} ${loading ? styles.submitLoading : ''}`}
        onClick={handleSubmit}
        disabled={loading}
      >
        {loading ? <span className={styles.spinner} /> : 'Crear cuenta'}
      </button>

      {/* Switch */}
      <p className={styles.switchText}>
        ¿Ya tienes cuenta?{' '}
        <button type="button" className={styles.switchLink} onClick={onSwitchToLogin}>
          Ingresar
        </button>
      </p>
    </div>
  )
}