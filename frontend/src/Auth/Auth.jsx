import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { Eye, EyeOff, Mail, Lock, User, AlertCircle, CheckCircle } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import LoginForm from './LoginForm'
import RegisterForm from './RegisterForm'
import styles from './Auth.module.css'

// Icono Google SVG inline
const GoogleIcon = () => (
  <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
    <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844a4.14 4.14 0 01-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615z" fill="#4285F4"/>
    <path d="M9 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 009 18z" fill="#34A853"/>
    <path d="M3.964 10.706A5.41 5.41 0 013.682 9c0-.593.102-1.17.282-1.706V4.962H.957A8.996 8.996 0 000 9c0 1.452.348 2.827.957 4.038l3.007-2.332z" fill="#FBBC05"/>
    <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 00.957 4.962L3.964 7.294C4.672 5.163 6.656 3.58 9 3.58z" fill="#EA4335"/>
  </svg>
)

export { GoogleIcon }

export default function Auth() {
  const [tab, setTab] = useState('login') // 'login' | 'register'
  const location = useLocation()

  // Si viene desde el carrito, recordar a dónde volver
  const from = location.state?.from || '/'

  return (
    <div className={styles.page}>
      {/* ── Panel izquierdo: formulario ─────────────────────────── */}
      <div className={styles.formPanel}>
        <div className={styles.formInner}>

          {/* Logo */}
          <Link to="/" className={styles.logo}>
            <span className={styles.logoIcon}>🪟</span>
            <div className={styles.logoText}>
              <span className={styles.logoTop}>PERSIANAS &amp; CORTINAS</span>
              <span className={styles.logoBottom}>DANY</span>
            </div>
          </Link>

          {/* Tabs */}
          <div className={styles.tabs}>
            <button
              className={`${styles.tab} ${tab === 'login' ? styles.tabActive : ''}`}
              onClick={() => setTab('login')}
            >
              Ingresar
            </button>
            <button
              className={`${styles.tab} ${tab === 'register' ? styles.tabActive : ''}`}
              onClick={() => setTab('register')}
            >
              Registrarse
            </button>
          </div>

          {/* Formularios */}
          {tab === 'login'
            ? <LoginForm from={from} onSwitchToRegister={() => setTab('register')} />
            : <RegisterForm from={from} onSwitchToLogin={() => setTab('login')} />
          }
        </div>
      </div>

      {/* ── Panel derecho: decorativo ───────────────────────────── */}
      <div className={styles.decorPanel}>
        <div className={styles.decorOverlay} />
        <div className={styles.decorContent}>
          <p className={styles.decorEyebrow}>Persianas &amp; Cortinas</p>
          <h2 className={styles.decorTitle}>
            <span>TRANSFORMA</span>
            <span>TU ESPACIO</span>
            <span className={styles.decorScript}>¡con estilo!</span>
          </h2>
          <p className={styles.decorSub}>
            Cortinas y persianas hechas a tu medida.<br/>
            Precio justo, entrega rápida, instalación incluida.
          </p>
          {/* Tarjetas de beneficios */}
          <div className={styles.decorCards}>
            {[
              { icon: '📐', label: 'A tu medida exacta' },
              { icon: '💳', label: 'Pago seguro en línea' },
              { icon: '🚚', label: 'Envío a todo el país' },
            ].map(c => (
              <div key={c.label} className={styles.decorCard}>
                <span>{c.icon}</span>
                <span>{c.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export { Eye, EyeOff, Mail, Lock, User, AlertCircle, CheckCircle, GoogleIcon as GIcon }