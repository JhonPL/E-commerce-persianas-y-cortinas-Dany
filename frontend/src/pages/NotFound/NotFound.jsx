import { Link, useNavigate } from 'react-router-dom'
import styles from './NotFound.module.css'

export default function NotFound() {
  const navigate = useNavigate()

  return (
    <div className={styles.page}>
      <div className={styles.inner}>

        <div className={styles.code}>404</div>

        <div className={styles.curtain}>
          <span className={styles.curtainLeft}>  🪟</span>
          <span className={styles.curtainRight}>🪟  </span>
        </div>

        <h1 className={styles.title}>Página no encontrada</h1>
        <p className={styles.sub}>
          Parece que esta página está detrás de las cortinas.<br />
          No la encontramos, pero podemos llevarte de vuelta.
        </p>

        <div className={styles.actions}>
          <Link to="/" className={styles.btnPrimary}>Ir al inicio</Link>
          <Link to="/tienda" className={styles.btnSecondary}>Ver productos</Link>
          <button className={styles.btnGhost} onClick={() => navigate(-1)}>← Volver atrás</button>
        </div>
      </div>
    </div>
  )
}