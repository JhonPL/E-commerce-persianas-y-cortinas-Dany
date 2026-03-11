import { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import styles from './Hero.module.css'

// Imagen de héroe — reemplazar por la imagen real del proyecto
const HERO_IMAGE = <img src='../public/img/32.webp' alt="Imagen Hero" />

export default function Hero() {
  const bgRef = useRef(null)

  // Efecto parallax suave en scroll
  useEffect(() => {
    const onScroll = () => {
      if (!bgRef.current) return
      const y = window.scrollY * 0.4
      bgRef.current.style.transform = `translateY(${y}px)`
    }
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <section className={styles.hero}>
      {/* Fondo con parallax */}
      <div className={styles.bgWrapper}>
        <div
          ref={bgRef}
          className={styles.bg}
          style={{ backgroundImage: `url(${HERO_IMAGE})` }}
        />
        <div className={styles.overlay} />
      </div>

      {/* Contenido */}
      <div className={styles.content}>
        <p className={styles.eyebrow}>Bienvenido</p>
        <h1 className={styles.title}>
          <span className={styles.titleMain}>TRANSFORMA</span>
          <span className={styles.titleMain}>TU HOGAR</span>
          <span className={styles.titleScript}>¡con estilo!</span>
        </h1>
        <p className={styles.subtitle}>
          Cortinas, persianas y accesorios decorativos hechos a tu medida
        </p>
        <div className={styles.ctas}>
          <Link to="/tienda" className={styles.ctaPrimary}>Ver colección</Link>
          <a
            href={`https://wa.me/573123558218?text=Hola, me gustaría recibir asesoría`}
            target="_blank"
            rel="noopener noreferrer"
            className={styles.ctaSecondary}
          >
            Solicitar asesoría
          </a>
        </div>
      </div>

      {/* Indicador de scroll */}
      <div className={styles.scrollHint}>
        <span className={styles.scrollLine} />
        <span className={styles.scrollLabel}>Explorar</span>
      </div>
    </section>
  )
}