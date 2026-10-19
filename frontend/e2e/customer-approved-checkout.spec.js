import { expect, test } from '@playwright/test'
import { addProductToCart, registerCustomer } from './support/customer.js'

test('el pago aprobado de prueba persiste el pedido y limpia el carrito', async ({ page }) => {
  await registerCustomer(page, 'approved')
  await addProductToCart(page)
  await page.getByRole('link', { name: 'Proceder al pago', exact: true }).click()

  await page.locator('input[name="departamento"]').fill('Meta')
  await page.locator('input[name="ciudad"]').fill('Granada')
  await page.locator('input[name="calle"]').fill('Dirección automatizada')
  await page.locator('input[name="numero"]').fill('100')
  await page.getByRole('radio', { name: /Aprobar pago de prueba/ }).check()

  const paymentRequest = page.waitForResponse((response) => {
    const request = response.request()
    return new URL(response.url()).pathname.endsWith('/payments/simulate/')
      && request.method() === 'POST'
  })
  await page.getByRole('button', { name: 'Crear pedido y simular pago' }).click()
  const paymentResponse = await paymentRequest
  expect(paymentResponse.ok(), await paymentResponse.text()).toBeTruthy()
  const payment = await paymentResponse.json()
  expect(payment.outcome).toBe('approved')

  await expect(page.getByRole('heading', { name: 'Pago aprobado (simulado)' })).toBeVisible()
  await expect(page.getByText('No se realizó ningún cobro ni se procesaron datos de tarjeta.')).toBeVisible()
  await expect(page.getByText(`Pedido #${payment.pedido_id}`, { exact: false })).toBeVisible()

  const cart = page.getByRole('dialog', { name: 'Carrito de compras' })
  await page.getByRole('button', { name: 'Carrito', exact: true }).click()
  await expect(cart).toContainText('Tu carrito está vacío')
  await page.keyboard.press('Escape')
  await expect(cart).not.toBeInViewport()

  const orderHistoryResponse = page.waitForResponse((response) => {
    const request = response.request()
    return new URL(response.url()).pathname.endsWith('/pedidos/')
      && request.method() === 'GET'
  })
  await page.getByRole('link', { name: 'Ver mis pedidos', exact: true }).click()
  const historyResponse = await orderHistoryResponse
  expect(historyResponse.ok()).toBeTruthy()
  const history = await historyResponse.json()
  expect(history.pedidos.some((order) => order.pedido_id === payment.pedido_id)).toBeTruthy()

  await expect(page.getByRole('heading', { name: 'Mis Pedidos' })).toBeVisible()
  await expect(page.getByRole('button', { name: new RegExp(`Pedido #${payment.pedido_id}`) })).toBeVisible()
})
