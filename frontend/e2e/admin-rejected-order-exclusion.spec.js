import { expect, test } from '@playwright/test'
import process from 'node:process'
import { addProductToCart, registerCustomer, rejectCheckout } from './support/customer.js'

const apiUrl = process.env.E2E_API_URL || 'http://127.0.0.1:8010/api/v1'

async function adminMetrics(page) {
  const token = await page.evaluate(() => localStorage.getItem('token'))
  const response = await page.request.get(`${apiUrl}/admin/dashboard/`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  expect(response.ok()).toBeTruthy()
  const data = await response.json()
  return {
    orders: data.metrics.pedidos_mes.value,
    income: data.metrics.ingresos_mes.value,
  }
}

async function loginAsAdmin(page, email, password) {
  await page.goto('/login')
  await page.getByPlaceholder('info@correo.com').fill(email)
  await page.getByPlaceholder('Ingresa tu contraseña').fill(password)
  await page.getByRole('button', { name: 'Ingresar', exact: true }).last().click()
  await expect(page).toHaveURL(/\/admin$/)
}

test('un pedido rechazado no aparece en administración ni modifica ventas', async ({ browser }) => {
  const adminEmail = process.env.E2E_ADMIN_EMAIL
  const adminPassword = process.env.E2E_ADMIN_PASSWORD
  expect(adminEmail, 'El ejecutor local debe crear un administrador temporal.').toBeTruthy()
  expect(adminPassword, 'El ejecutor local debe crear un administrador temporal.').toBeTruthy()

  const baseURL = process.env.E2E_BASE_URL || 'http://127.0.0.1:5173'
  const adminContext = await browser.newContext({ baseURL })
  const customerContext = await browser.newContext({ baseURL })
  const adminPage = await adminContext.newPage()
  const customerPage = await customerContext.newPage()

  try {
    await adminPage.goto('/login')
    await adminPage.getByPlaceholder('info@correo.com').fill(adminEmail)
    await adminPage.getByPlaceholder('Ingresa tu contraseña').fill('Invalid-E2E-Password!')
    await adminPage.getByRole('button', { name: 'Ingresar', exact: true }).last().click()
    await expect(adminPage).toHaveURL(/\/login$/)
    await expect(adminPage.locator('[class*="alertError"]')).toBeVisible()
    await loginAsAdmin(adminPage, adminEmail, adminPassword)
    const before = await adminMetrics(adminPage)

    const email = await registerCustomer(customerPage, 'admin-exclusion')
    await addProductToCart(customerPage)
    await rejectCheckout(customerPage)

    await adminPage.goto('/admin/pedidos')
    const filteredOrdersResponse = adminPage.waitForResponse((response) => {
      const url = new URL(response.url())
      return url.pathname.endsWith('/admin/pedidos/')
        && url.searchParams.get('search') === email
        && response.request().method() === 'GET'
    })
    await adminPage.getByPlaceholder('Buscar por cliente o #pedido…').fill(email)
    const response = await filteredOrdersResponse
    expect(response.ok()).toBeTruthy()
    const filteredOrders = await response.json()
    expect(filteredOrders.pedidos).toHaveLength(0)
    await expect(adminPage.getByText('Sin resultados')).toBeVisible()
    await expect(adminPage.getByText(email, { exact: false })).toHaveCount(0)

    await adminPage.goto('/admin')
    const after = await adminMetrics(adminPage)
    expect(after).toEqual(before)
  } finally {
    await customerContext.close()
    await adminContext.close()
  }
})
