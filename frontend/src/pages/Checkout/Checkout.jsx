import { useState } from 'react'
import { Link } from 'react-router-dom'
import { AlertCircle, CheckCircle2, CreditCard, ShieldCheck } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { useCart } from '../../context/CartContext'
import { API_URL } from '../../config/api'
import styles from './Checkout.module.css'

const formatCOP = (value) =>
  new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    maximumFractionDigits: 0,
  }).format(value)

async function readResponse(response) {
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    const detail = data.detail || Object.values(data).flat()[0]
    throw new Error(detail || 'No fue posible completar la operación.')
  }
  return data
}

export default function Checkout() {
  const { user, token } = useAuth()
  const { items, total, clearCart } = useCart()
  const [address, setAddress] = useState({
    departamento: '',
    ciudad: '',
    barrio: '',
    calle: '',
    numero: '',
    complemento: '',
  })
  const [outcome, setOutcome] = useState('approved')
  const [order, setOrder] = useState(null)
  const [payment, setPayment] = useState(null)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const updateAddress = (event) => {
    const { name, value } = event.target
    setAddress((current) => ({ ...current, [name]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setSubmitting(true)

    try {
      let currentOrder = order
      if (!currentOrder) {
        const response = await fetch(`${API_URL}/pedidos/checkout/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ direccion: address }),
        })
        currentOrder = await readResponse(response)
        setOrder(currentOrder)
      }

      const response = await fetch(`${API_URL}/payments/simulate/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          pedido_id: currentOrder.pedido_id,
          outcome,
          request_id: window.crypto.randomUUID(),
        }),
      })
      const paymentResult = await readResponse(response)
      setPayment(paymentResult)
      if (paymentResult.outcome === 'approved') {
        await clearCart()
      }
    } catch (requestError) {
      setError(requestError.message || 'No fue posible completar el pago simulado.')
    } finally {
      setSubmitting(false)
    }
  }

  if (payment?.outcome === 'approved') {
    return (
      <main className={styles.page}>
        <section className={styles.resultCard} role="status">
          <CheckCircle2 className={styles.successIcon} size={44} />
          <p className={styles.eyebrow}>Simulación completada</p>
          <h1>Pago aprobado (simulado)</h1>
          <p>
            El pedido <strong>#{payment.pedido_id}</strong> quedó registrado por{' '}
            <strong>{formatCOP(Number(payment.amount))}</strong>.
          </p>
          <p className={styles.notice}>
            No se realizó ningún cobro ni se procesaron datos de tarjeta.
          </p>
          <Link className={styles.primaryButton} to="/mis-pedidos">
            Ver mis pedidos
          </Link>
        </section>
      </main>
    )
  }

  return (
    <main className={styles.page}>
      <div className={styles.heading}>
        <p className={styles.eyebrow}>Finalizar compra</p>
        <h1>Entrega y pago de prueba</h1>
        <p>Completa la dirección y elige el resultado del simulador.</p>
      </div>

      {items.length === 0 && !order ? (
        <section className={styles.resultCard}>
          <h2>Tu carrito está vacío</h2>
          <Link className={styles.primaryButton} to="/tienda">
            Volver a la tienda
          </Link>
        </section>
      ) : payment?.outcome === 'declined' ? (
        <section className={styles.resultCard} role="status">
          <AlertCircle className={styles.errorIcon} size={42} />
          <p className={styles.eyebrow}>Pedido #{payment.pedido_id}</p>
          <h2>Pago rechazado (simulado)</h2>
          <p>No se hizo ningún cobro. Puedes probar nuevamente con otro resultado.</p>
          <button
            className={styles.secondaryButton}
            type="button"
            onClick={() => setPayment(null)}
          >
            Reintentar simulación
          </button>
        </section>
      ) : (
        <div className={styles.layout}>
          <form className={styles.form} onSubmit={handleSubmit}>
            <section className={styles.panel}>
              <h2>Dirección de entrega</h2>
              <p className={styles.customer}>Pedido para {user?.nombre || user?.email}</p>
              <div className={styles.fields}>
                {[
                  ['departamento', 'Departamento'],
                  ['ciudad', 'Ciudad o municipio'],
                  ['barrio', 'Barrio (opcional)'],
                  ['calle', 'Dirección / calle'],
                  ['numero', 'Número'],
                  ['complemento', 'Complemento (opcional)'],
                ].map(([name, label]) => (
                  <label className={styles.field} key={name}>
                    <span>{label}</span>
                    <input
                      name={name}
                      value={address[name]}
                      onChange={updateAddress}
                      required={!['barrio', 'complemento'].includes(name)}
                      disabled={Boolean(order)}
                      maxLength={150}
                    />
                  </label>
                ))}
              </div>
            </section>

            <section className={styles.panel}>
              <h2><CreditCard size={19} /> Simulador de pago</h2>
              <p className={styles.notice}>
                Demostración sin pasarela real. No ingreses información de tarjetas.
              </p>
              <label className={styles.choice}>
                <input
                  type="radio"
                  name="outcome"
                  value="approved"
                  checked={outcome === 'approved'}
                  onChange={(event) => setOutcome(event.target.value)}
                />
                <span>
                  <strong>Aprobar pago de prueba</strong>
                  <small>Continúa el pedido como si hubiera sido aprobado.</small>
                </span>
              </label>
              <label className={styles.choice}>
                <input
                  type="radio"
                  name="outcome"
                  value="declined"
                  checked={outcome === 'declined'}
                  onChange={(event) => setOutcome(event.target.value)}
                />
                <span>
                  <strong>Rechazar pago de prueba</strong>
                  <small>Prueba el flujo de rechazo, sin crear un cobro.</small>
                </span>
              </label>
              <p className={styles.securityNote}>
                <ShieldCheck size={16} /> No se guardan datos de pago reales.
              </p>
            </section>

            {error && <p className={styles.errorMessage} role="alert">{error}</p>}
            <button className={styles.primaryButton} type="submit" disabled={submitting}>
              {submitting
                ? 'Procesando simulación…'
                : order
                  ? 'Reintentar simulación'
                  : 'Crear pedido y simular pago'}
            </button>
          </form>

          <aside className={styles.panel}>
            <h2>Resumen del pedido</h2>
            <ul className={styles.items}>
              {items.map((item) => (
                <li key={item.key}>
                  <span>{item.cantidad} × {item.product.nombre}</span>
                  <strong>{formatCOP(item.precioTotal)}</strong>
                </li>
              ))}
            </ul>
            <div className={styles.total}>
              <span>Total calculado por el servicio</span>
              <strong>{formatCOP(order ? Number(order.total) : total)}</strong>
            </div>
            {order && (
              <p className={styles.notice}>
                Pedido #{order.pedido_id} creado; el carrito se conserva hasta la aprobación.
              </p>
            )}
          </aside>
        </div>
      )}
    </main>
  )
}