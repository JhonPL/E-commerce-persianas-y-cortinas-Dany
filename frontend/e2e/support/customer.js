import { expect } from '@playwright/test'
import process from 'node:process'

const runId = process.env.E2E_RUN_ID

if (!runId) {
  throw new Error('Ejecuta las pruebas con frontend\\run-e2e-local.ps1 para aislar sus datos.')
}

export function customerEmail(flow) {
  return `e2e.${runId}.${flow}@example.test`
}

export async function registerCustomer(page, flow) {
  const email = customerEmail(flow)
  await page.goto('/login')
  await page.getByRole('button', { name: 'Registrarse', exact: true }).click()
  await page.getByPlaceholder('Tu nombre').fill(`Cliente E2E ${flow}`)
  await page.getByPlaceholder('info@correo.com').fill(email)
  await page.getByPlaceholder('Mínimo 8 caracteres').fill('E2e-Test-Local-2026!')
  await page.getByPlaceholder('Repite tu contraseña').fill('E2e-Test-Local-2026!')
  await page.locator('input[type="checkbox"]').check()
  await page.getByRole('button', { name: 'Crear cuenta', exact: true }).click()
  await expect(page.getByRole('heading', { name: '¡Cuenta creada!' })).toBeVisible()
  await page.getByRole('button', { name: 'Continuar' }).click()
  await expect(page.getByRole('button', { name: 'Mi cuenta' })).toBeVisible()
  return email
}

export async function addProductToCart(page) {
  await page.goto('/producto/1')
  await expect(page.getByRole('heading', { name: 'Cortina en velo' })).toBeVisible()
  await page.locator('input[type="number"]').nth(0).fill('100')
  await page.locator('input[type="number"]').nth(1).fill('100')
  await expect(page.getByText('1.0000 m²')).toBeVisible()
  const cartSave = page.waitForResponse((response) => {
    const request = response.request()
    return new URL(response.url()).pathname.endsWith('/carrito/')
      && request.method() === 'POST'
  })
  await page.getByRole('button', { name: 'Agregar al carrito' }).click()
  const saveResponse = await cartSave
  expect(saveResponse.ok(), await saveResponse.text()).toBeTruthy()
  await expect(page.getByRole('dialog', { name: 'Carrito de compras' })).toContainText('100 × 100 cm')
}

export async function rejectCheckout(page) {
  await page.getByRole('link', { name: 'Proceder al pago', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Entrega y pago de prueba' })).toBeVisible()
  await page.locator('select[name="departamento"]').selectOption({ label: 'Meta' })
  await page.locator('select[name="ciudad"]').selectOption({ label: 'Granada' })
  await page.locator('input[name="nombre_recibe"]').fill('Persona receptora')
  await page.locator('input[name="barrio"]').fill('Centro')
  await page.locator('textarea[name="calle"]').fill('Carrera 10 # 20-52, apartamento 301')
  await page.getByRole('radio', { name: /Rechazar pago de prueba/ }).check()
  const paymentRequest = page.waitForResponse((response) => {
    const request = response.request()
    return new URL(response.url()).pathname.endsWith('/payments/simulate/')
      && request.method() === 'POST'
  })
  await page.getByRole('button', { name: 'Crear pedido y simular pago' }).click()
  const paymentResponse = await paymentRequest
  expect(paymentResponse.ok(), await paymentResponse.text()).toBeTruthy()
  const paymentResult = await paymentResponse.json()
  await expect(page.getByRole('heading', { name: 'Pago rechazado (simulado)' })).toBeVisible()
  await expect(page.getByText('No se hizo ningún cobro.')).toBeVisible()
  return paymentResult.pedido_id
}
