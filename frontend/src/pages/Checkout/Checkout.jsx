import { useState } from 'react'
import { Link } from 'react-router-dom'
import { AlertCircle, CheckCircle2, CreditCard, LoaderCircle, ShieldCheck } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { useCart } from '../../context/CartContext'
import { API_URL } from '../../config/api'
import { downloadOrderInvoice } from '../../api/invoices'
import colombiaLocations from '../../data/colombiaLocations.json'
import styles from './Checkout.module.css'

const departments = colombiaLocations
  .map((department) => ({
    ...department,
    ciudades: [...department.ciudades].sort((a, b) => a.localeCompare(b, 'es')),
  }))
  .sort((a, b) => a.departamento.localeCompare(b.departamento, 'es'))

const addressFieldLabels = {
  departamento: 'Departamento',
  ciudad: 'Ciudad o municipio',
  nombre_recibe: 'Nombre de quien recibe',
  barrio: 'Barrio',
  calle: 'Dirección completa',
  numero: 'Número',
}

const demoCards = {
  approved: '4242424242424242',
  declined: '4000000000000002',
}

const emptyCard = { holder: '', number: '', expiry: '', cvc: '' }

const formatCOP = (value) =>
  new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    maximumFractionDigits: 0,
  }).format(value)

async function readResponse(response) {
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    const fieldError = Object.entries(data).find(([field, messages]) =>
      field !== 'detail' && Array.isArray(messages) && messages.length > 0,
    )
    const detail = data.detail || (fieldError
      ? `${addressFieldLabels[fieldError[0]] || fieldError[0]}: ${fieldError[1][0]}`
      : Object.values(data).flat()[0])
    throw new Error(detail || 'No fue posible completar la operación.')
  }
  return data
}

export default function Checkout() {
  const { user, authenticatedFetch } = useAuth()
  const { items, total, clearCart } = useCart()
  const [address, setAddress] = useState({
    departamento: '',
    ciudad: '',
    nombre_recibe: '',
    barrio: '',
    calle: '',
  })
  const [card, setCard] = useState(emptyCard)
  const [order, setOrder] = useState(null)
  const [payment, setPayment] = useState(null)
  const [error, setError] = useState('')
  const [invoiceError, setInvoiceError] = useState('')
  const [downloadingInvoice, setDownloadingInvoice] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const updateAddress = (event) => {
    const { name, value } = event.target
    setAddress((current) => ({
      ...current,
      [name]: value,
      ...(name === 'departamento' ? { ciudad: '' } : {}),
    }))
  }

  const updateCard = (event) => {
    const { name, value } = event.target
    let nextValue = value
    if (name === 'number') {
      nextValue = value.replace(/\D/g, '').slice(0, 16).replace(/(.{4})/g, '$1 ').trim()
    } else if (name === 'expiry') {
      const digits = value.replace(/\D/g, '').slice(0, 4)
      nextValue = digits.length > 2 ? `${digits.slice(0, 2)}/${digits.slice(2)}` : digits
    } else if (name === 'cvc') {
      nextValue = value.replace(/\D/g, '').slice(0, 3)
    }
    setCard((current) => ({ ...current, [name]: nextValue }))
  }

  const downloadInvoice = async () => {
    setDownloadingInvoice(true)
    setInvoiceError('')
    try {
      await downloadOrderInvoice(authenticatedFetch, payment.pedido_id)
    } catch (downloadError) {
      setInvoiceError(downloadError.message)
    } finally {
      setDownloadingInvoice(false)
    }
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setSubmitting(true)

    try {
      const cardNumber = card.number.replace(/\D/g, '')
      const outcome = Object.entries(demoCards).find(([, number]) => number === cardNumber)?.[0]
      if (!outcome) {
        throw new Error('Usa uno de los números de tarjeta de prueba indicados en pantalla.')
      }
      const [month, year] = card.expiry.split('/').map(Number)
      const expiration = new Date(2000 + year, month)
      const currentMonth = new Date()
      currentMonth.setDate(1)
      currentMonth.setHours(0, 0, 0, 0)
      if (!month || month > 12 || expiration <= currentMonth) {
        throw new Error('La fecha de vencimiento de prueba no es válida.')
      }
      setCard(emptyCard)

      let currentOrder = order
      if (!currentOrder) {
        const response = await authenticatedFetch(`${API_URL}/pedidos/checkout/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ direccion: address }),
        })
        currentOrder = await readResponse(response)
        setOrder(currentOrder)
      }

      await new Promise((resolve) => window.setTimeout(resolve, 2000))
      const response = await authenticatedFetch(`${API_URL}/payments/simulate/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
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
          <h1>¡Pago completado con éxito!</h1>
          <p>
            El pedido <strong>#{payment.pedido_id}</strong> quedó registrado por{' '}
            <strong>{formatCOP(Number(payment.amount))}</strong>.
          </p>
          <p className={styles.notice}>
            No se realizó ningún cobro ni se procesaron datos de tarjeta.
          </p>
          <p className={styles.notice}>
            {payment.notification === 'enviado'
              ? 'La factura PDF de demostración fue enviada al correo de tu cuenta y al administrador.'
              : 'El pago quedó aprobado, pero no se pudo confirmar el envío del correo. Puedes intentar descargar el PDF aquí.'}
          </p>
          <button
            className={styles.secondaryButton}
            type="button"
            onClick={downloadInvoice}
            disabled={downloadingInvoice}
          >
            {downloadingInvoice ? 'Generando PDF…' : 'Descargar factura PDF'}
          </button>
          {invoiceError && <p className={styles.errorMessage} role="alert">{invoiceError}</p>}
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
        <p>Confirma la entrega y paga con una tarjeta ficticia de demostración.</p>
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
                <label className={styles.field}>
                  <span>Departamento</span>
                  <select
                    name="departamento"
                    value={address.departamento}
                    onChange={updateAddress}
                    required
                    disabled={Boolean(order)}
                  >
                    <option value="">Selecciona un departamento</option>
                    {departments.map((department) => (
                      <option key={department.departamento} value={department.departamento}>
                        {department.departamento}
                      </option>
                    ))}
                  </select>
                </label>
                <label className={styles.field}>
                  <span>Ciudad o municipio</span>
                  <select
                    name="ciudad"
                    value={address.ciudad}
                    onChange={updateAddress}
                    required
                    disabled={Boolean(order) || !address.departamento}
                  >
                    <option value="">
                      {address.departamento ? 'Selecciona una ciudad o municipio' : 'Primero selecciona un departamento'}
                    </option>
                    {departments
                      .find((department) => department.departamento === address.departamento)
                      ?.ciudades.map((city) => (
                        <option key={city} value={city}>{city}</option>
                      ))}
                  </select>
                </label>
                <label className={styles.field}>
                  <span>Nombre de quien recibe</span>
                  <input
                    name="nombre_recibe"
                    value={address.nombre_recibe}
                    onChange={updateAddress}
                    required
                    disabled={Boolean(order)}
                    maxLength={100}
                  />
                </label>
                <label className={styles.field}>
                  <span>Barrio</span>
                  <input
                    name="barrio"
                    value={address.barrio}
                    onChange={updateAddress}
                    required
                    disabled={Boolean(order)}
                    maxLength={100}
                  />
                </label>
                <label className={`${styles.field} ${styles.fullWidth}`}>
                  <span>Dirección completa</span>
                  <small>Incluye tipo de vía, número, apartamento, interior u otras indicaciones.</small>
                  <textarea
                    name="calle"
                    value={address.calle}
                    onChange={updateAddress}
                    required
                    disabled={Boolean(order)}
                    maxLength={150}
                    minLength={5}
                    rows={3}
                    autoComplete="street-address"
                  />
                </label>
              </div>
            </section>

            <section className={styles.panel}>
              <h2><CreditCard size={19} /> Pago con tarjeta de prueba</h2>
              <p className={styles.notice}>
                Simulación académica: usa únicamente los datos ficticios indicados aquí.
                Ningún dato de tarjeta se envía ni se almacena.
              </p>
              <div className={styles.cardPreview} aria-hidden="true">
                <div className={styles.cardPreviewTop}>
                  <span>PERSIANAS &amp; CORTINAS DANY</span>
                  <CreditCard size={24} />
                </div>
                <strong>{card.number || '•••• •••• •••• ••••'}</strong>
                <div className={styles.cardPreviewFooter}>
                  <span>{card.holder || 'NOMBRE DEL TITULAR'}</span>
                  <span>{card.expiry || 'MM/AA'}</span>
                </div>
              </div>
              <div className={styles.fields}>
                <label className={`${styles.field} ${styles.fullWidth}`}>
                  <span>Nombre del titular</span>
                  <input
                    name="holder"
                    value={card.holder}
                    onChange={updateCard}
                    autoComplete="off"
                    maxLength={80}
                    required
                    disabled={submitting}
                  />
                </label>
                <label className={`${styles.field} ${styles.fullWidth}`}>
                  <span>Número de tarjeta de prueba</span>
                  <input
                    name="number"
                    value={card.number}
                    onChange={updateCard}
                    inputMode="numeric"
                    autoComplete="off"
                    placeholder="4242 4242 4242 4242"
                    maxLength={19}
                    required
                    disabled={submitting}
                  />
                </label>
                <label className={styles.field}>
                  <span>Vencimiento</span>
                  <input
                    name="expiry"
                    value={card.expiry}
                    onChange={updateCard}
                    inputMode="numeric"
                    autoComplete="off"
                    placeholder="MM/AA"
                    pattern="[0-9]{2}/[0-9]{2}"
                    title="Usa el formato MM/AA"
                    maxLength={5}
                    required
                    disabled={submitting}
                  />
                </label>
                <label className={styles.field}>
                  <span>Código de seguridad</span>
                  <input
                    name="cvc"
                    value={card.cvc}
                    onChange={updateCard}
                    inputMode="numeric"
                    autoComplete="off"
                    placeholder="123"
                    pattern="[0-9]{3}"
                    maxLength={3}
                    required
                    disabled={submitting}
                  />
                </label>
              </div>
              <div className={styles.demoCards}>
                <p><strong>Aprobación:</strong> 4242 4242 4242 4242</p>
                <p><strong>Rechazo:</strong> 4000 0000 0000 0002</p>
                <p>Usa cualquier vencimiento futuro y un código ficticio de 3 dígitos.</p>
              </div>
              <p className={styles.securityNote}>
                <ShieldCheck size={16} /> Solo se envía al servidor el resultado simulado.
              </p>
            </section>

            {error && <p className={styles.errorMessage} role="alert">{error}</p>}
            <button className={styles.primaryButton} type="submit" disabled={submitting}>
              {submitting
                ? <><LoaderCircle className={styles.processingIcon} size={18} /> Procesando pago…</>
                : order
                  ? 'Reintentar pago de prueba'
                  : 'Pagar ahora'}
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