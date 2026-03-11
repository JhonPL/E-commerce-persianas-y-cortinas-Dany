import { Link } from 'react-router-dom'
import styles from './Footer.module.css'

export default function Footer() {
  return (
    <footer className={styles.footer}>
      <div className={styles.inner}>
        {/* Brand */}
        <div className={styles.brand}>
          <span className={styles.brandName}>PERSIANAS &amp; CORTINAS DANY</span>
          <p className={styles.brandTagline}>Transformamos tu espacio con elegancia</p>
        </div>

        {/* Links */}
        <nav className={styles.links}>
          <Link to="/">Inicio</Link>
          <Link to="/tienda">Tienda</Link>
          <Link to="/contacto">Contacto</Link>
        </nav>

        {/* Contacto */}
        <div className={styles.contact}>
          <a
            href="https://wa.me/573001234567"
            target="_blank"
            rel="noopener noreferrer"
            className={styles.contactLink}
          >
            WhatsApp
          </a>
          <span className={styles.contactDivider}>·</span>
          <a href="mailto:percortinasdany@gmail.com" className={styles.contactLink}>
            percortinasdany@gmail.com
          </a>
        </div>
      </div>

      <div className={styles.bottom}>
        <p>© {new Date().getFullYear()} Persianas &amp; Cortinas Dany — Villavicencio, Meta</p>
      </div>
    </footer>
  )
}