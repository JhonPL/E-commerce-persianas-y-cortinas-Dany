import { expect, test } from '@playwright/test'

test('el formulario de contacto envía los datos al gateway', async ({ page }) => {
  let submittedPayload
  await page.route('**/api/v1/contacto/', async (route) => {
    submittedPayload = route.request().postDataJSON()
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ estado: 'enviado' }),
    })
  })

  await page.goto('/contacto')
  await page.locator('#contact-name').fill('Cliente E2E')
  await page.locator('#contact-email').fill('cliente@example.test')
  await page.locator('#contact-subject').fill('Consulta E2E')
  await page.locator('#contact-message').fill('Mensaje de prueba del formulario.')
  await page.getByRole('button', { name: 'Enviar mensaje' }).click()

  await expect(page.getByRole('heading', { name: '¡Mensaje enviado!' })).toBeVisible()
  expect(submittedPayload).toEqual({
    nombre: 'Cliente E2E',
    email: 'cliente@example.test',
    asunto: 'Consulta E2E',
    mensaje: 'Mensaje de prueba del formulario.',
  })
})

test('el formulario de contacto informa si el correo no se pudo enviar', async ({ page }) => {
  await page.route('**/api/v1/contacto/', async (route) => {
    await route.fulfill({
      status: 502,
      contentType: 'application/json',
      body: JSON.stringify({ detail: 'No fue posible enviar el mensaje. Inténtalo de nuevo.' }),
    })
  })

  await page.goto('/contacto')
  await page.locator('#contact-name').fill('Cliente E2E')
  await page.locator('#contact-email').fill('cliente@example.test')
  await page.locator('#contact-message').fill('Mensaje de prueba del formulario.')
  await page.getByRole('button', { name: 'Enviar mensaje' }).click()

  await expect(page.getByRole('alert')).toHaveText(
    'No fue posible enviar el mensaje. Inténtalo de nuevo.',
  )
  await expect(page.getByRole('heading', { name: 'Envíanos un mensaje' })).toBeVisible()
})
