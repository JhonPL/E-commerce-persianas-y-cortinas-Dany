import { API_URL } from '../config/api'

export async function downloadOrderInvoice(authenticatedFetch, orderId) {
  const response = await authenticatedFetch(
    `${API_URL}/pedidos/${orderId}/factura/`,
  )
  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new Error(
      data.detail || 'No fue posible descargar el documento de este pedido.',
    )
  }

  const pdf = await response.blob()
  if (pdf.type !== 'application/pdf' || pdf.size === 0) {
    throw new Error('El servicio devolvió un documento PDF no válido.')
  }

  const url = window.URL.createObjectURL(pdf)
  const link = document.createElement('a')
  link.href = url
  link.download = `DEMO-${String(orderId).padStart(6, '0')}.pdf`
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.setTimeout(() => window.URL.revokeObjectURL(url), 1000)
}
