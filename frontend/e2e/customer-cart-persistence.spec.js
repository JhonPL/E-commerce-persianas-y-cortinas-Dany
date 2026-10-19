import { expect, test } from '@playwright/test'
import { addProductToCart, registerCustomer } from './support/customer.js'

test('el carrito del cliente persiste al recargar y puede limpiarse', async ({ page }) => {
  await registerCustomer(page, 'cart')
  await addProductToCart(page)

  const cartSync = page.waitForResponse((response) => {
    const request = response.request()
    return new URL(response.url()).pathname.endsWith('/carrito/sincronizar/')
      && request.method() === 'POST'
  })
  await page.reload()
  const syncResponse = await cartSync
  expect(syncResponse.ok(), await syncResponse.text()).toBeTruthy()
  const cart = page.getByRole('dialog', { name: 'Carrito de compras' })
  await page.getByRole('button', { name: 'Carrito', exact: true }).click()
  await expect(cart).toContainText('Cortina en velo')
  await expect(cart).toContainText('100 × 100 cm')
  const removeItem = cart.getByRole('button', { name: 'Eliminar Cortina en velo' })
  await expect(removeItem).toBeInViewport()
  await removeItem.click()
  await expect(cart).toContainText('Tu carrito está vacío')
})
