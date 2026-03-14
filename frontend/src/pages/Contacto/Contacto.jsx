import { useState } from 'react'
import { MapPin, Phone, Mail, Clock, Send, CheckCircle, MessageCircle } from 'lucide-react'
import styles from './Contacto.module.css'

const WHATSAPP = '573001234567'

export default function Contacto() {
  const [form, setForm]     = useState({ nombre: '', email: '', asunto: '', mensaje: '' })
  const [errors, setErrors] = useState({})
  const [sent, setSent]     = useState(false)
  const [loading, setLoading] = useState(false)

  const f = (k, v) => { setForm(p => ({ ...p, [k]: v })); setErrors(p => ({ ...p, [k]: '' })) }

  const validate = () => {
    const e = {}
    if (!form.nombre.trim())  e.nombre  = 'Requerido'
    if (!form.email.trim())   e.email   = 'Requerido'
    else if (!/\S+@\S+\.\S+/.test(form.email)) e.email = 'Correo inválido'
    if (!form.mensaje.trim()) e.mensaje = 'Escribe tu mensaje'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const handleSubmit = async () => {
    if (!validate()) return
    setLoading(true)
    // TODO: POST /api/contacto
    await new Promise(r => setTimeout(r, 1000))
    setLoading(false)
    setSent(true)
  }

  const handleWhatsApp = () => {
    const msg = encodeURIComponent('Hola, quisiera información sobre sus productos.')
    window.open(`https://wa.me/${WHATSAPP}?text=${msg}`, '_blank')
  }

  return (
    <div className={styles.page}>

      {/* ── Hero ─────────────────────────────────────────── */}
      <section className={styles.hero}>
        <div className={styles.heroOverlay} />
        <div className={styles.heroContent}>
          <p className={styles.eyebrow}>Estamos para ayudarte</p>
          <h1 className={styles.heroTitle}>Contáctanos</h1>
          <p className={styles.heroSub}>
            Escríbenos, llámanos o visítanos. Con gusto te asesoramos<br />
            para encontrar la solución perfecta para tu hogar.
          </p>
        </div>
      </section>

      {/* ── Info + Formulario ────────────────────────────── */}
      <section className={styles.body}>
        <div className={styles.bodyInner}>

          {/* Columna izquierda: datos */}
          <div className={styles.infoCol}>
            <h2 className={styles.infoTitle}>Información de contacto</h2>

            <div className={styles.infoCards}>
              {[
                { icon: MapPin,  label: 'Dirección',  value: 'Calle 35 # 28-14, Villavicencio, Meta' },
                { icon: Phone,   label: 'Teléfono',   value: '+57 300 123 4567' },
                { icon: Mail,    label: 'Correo',     value: 'ventas@cortinasydany.com' },
                { icon: Clock,   label: 'Horario',    value: 'Lun – Sáb: 8:00 am – 6:00 pm' },
              ].map(({ icon: Icon, label, value }) => (
                <div key={label} className={styles.infoCard}>
                  <div className={styles.infoCardIcon}><Icon size={18} /></div>
                  <div>
                    <span className={styles.infoCardLabel}>{label}</span>
                    <span className={styles.infoCardValue}>{value}</span>
                  </div>
                </div>
              ))}
            </div>

            {/* WhatsApp directo */}
            <button className={styles.waBtn} onClick={handleWhatsApp}>
              <MessageCircle size={18} />
              Escríbenos por WhatsApp
            </button>

            {/* Mapa embed (placeholder — reemplazar con Google Maps embed real) */}
            <div className={styles.mapWrapper}>
              <iframe
                title="Ubicación Persianas y Cortinas Dany"
                src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d15935.01!2d-73.6366!3d4.1420!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x8e3e2e!2sVillavicencio!5e0!3m2!1ses!2sco!4v1"
                width="100%"
                height="200"
                style={{ border: 0, borderRadius: 8 }}
                allowFullScreen=""
                loading="lazy"
                referrerPolicy="no-referrer-when-downgrade"
              />
            </div>
          </div>

          {/* Columna derecha: formulario */}
          <div className={styles.formCol}>
            {sent ? (
              <div className={styles.successBox}>
                <CheckCircle size={48} color="#8fc263" />
                <h3 className={styles.successTitle}>¡Mensaje enviado!</h3>
                <p className={styles.successSub}>
                  Gracias por contactarnos. Te responderemos en menos de 24 horas.
                </p>
                <button className={styles.btnPrimary} onClick={() => { setSent(false); setForm({ nombre: '', email: '', asunto: '', mensaje: '' }) }}>
                  Enviar otro mensaje
                </button>
              </div>
            ) : (
              <>
                <h2 className={styles.formTitle}>Envíanos un mensaje</h2>
                <p className={styles.formSub}>Completa el formulario y te contactamos pronto.</p>

                <div className={styles.formGrid}>
                  <div className={styles.field}>
                    <label className={styles.label}>Nombre <span className={styles.req}>*</span></label>
                    <input className={`${styles.input} ${errors.nombre ? styles.inputErr : ''}`}
                      placeholder="Tu nombre completo" value={form.nombre}
                      onChange={e => f('nombre', e.target.value)} />
                    {errors.nombre && <span className={styles.fieldErr}>{errors.nombre}</span>}
                  </div>

                  <div className={styles.field}>
                    <label className={styles.label}>Correo electrónico <span className={styles.req}>*</span></label>
                    <input className={`${styles.input} ${errors.email ? styles.inputErr : ''}`}
                      type="email" placeholder="tu@correo.com" value={form.email}
                      onChange={e => f('email', e.target.value)} />
                    {errors.email && <span className={styles.fieldErr}>{errors.email}</span>}
                  </div>

                  <div className={`${styles.field} ${styles.fieldFull}`}>
                    <label className={styles.label}>Asunto</label>
                    <input className={styles.input}
                      placeholder="¿En qué podemos ayudarte?" value={form.asunto}
                      onChange={e => f('asunto', e.target.value)} />
                  </div>

                  <div className={`${styles.field} ${styles.fieldFull}`}>
                    <label className={styles.label}>Mensaje <span className={styles.req}>*</span></label>
                    <textarea className={`${styles.input} ${styles.textarea} ${errors.mensaje ? styles.inputErr : ''}`}
                      placeholder="Escribe tu consulta aquí..." rows={5}
                      value={form.mensaje} onChange={e => f('mensaje', e.target.value)} />
                    {errors.mensaje && <span className={styles.fieldErr}>{errors.mensaje}</span>}
                  </div>
                </div>

                <button
                  className={`${styles.btnPrimary} ${loading ? styles.btnLoading : ''}`}
                  onClick={handleSubmit} disabled={loading}
                >
                  {loading
                    ? <span className={styles.spinner} />
                    : <><Send size={15} /> Enviar mensaje</>
                  }
                </button>
              </>
            )}
          </div>
        </div>
      </section>
    </div>
  )
}