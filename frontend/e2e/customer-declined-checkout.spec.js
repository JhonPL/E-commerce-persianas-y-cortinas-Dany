import { expect, test } from '@playwright/test'
import { addProductToCart, registerCustomer, rejectCheckout } from './support/customer.js'

test('el rechazo simulado conserva el carrito y el pedido queda en el historial del cliente', async ({ page }) => {
  await registerCustomer(page, 'declined')
  await addProductToCart(page)
  const orderId = await rejectCheckout(page)

  expect(orderId).toBeTruthy()
  await page.getByRole('button', { name: 'Carrito', exact: true }).click()
  await expect(page.getByRole('dialog', { name: 'Carrito de compras' })).toContainText('Cortina en velo')

  await page.goto('/mis-pedidos')
  await expect(page.getByRole('heading', { name: 'Mis Pedidos' })).toBeVisible()
  await expect(page.getByText(`Pedido #${orderId}`, { exact: false })).toBeVisible()
  await expect(page.getByText('Pago rechazado', { exact: false })).toBeVisible()
})
