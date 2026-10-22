import { expect, test } from '@playwright/test'

test('home presents a local sample and sign-in entry', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Lango Learn', exact: true })).toBeVisible()
  await expect(page.getByText('Local sample · Spanish greetings')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Sign in with GitHub' })).toBeVisible()
})

test('about route keeps the guest sign-in entry', async ({ page }) => {
  await page.goto('/about')
  await expect(page).toHaveURL(/\/about$/)
  await expect(page.getByRole('heading', { name: 'About Lango Learn' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Sign in with GitHub' })).toBeVisible()
})

test('sample stays local through reload and never calls a write action', async ({ page, context }) => {
  const writes: string[] = []
  page.on('request', request => {
    if (request.method() === 'POST' && request.url().includes('/actions/')) writes.push(request.url())
  })
  await page.goto('/')
  await page.getByRole('button', { name: 'Start local sample' }).click()
  await page.getByRole('button', { name: 'Hello' }).click()
  await expect(page.getByText('Step 2 of 2')).toBeVisible()
  await page.reload()
  await expect(page.getByText('Step 2 of 2')).toBeVisible()
  await page.getByRole('button', { name: 'Thank you' }).click()
  await expect(page.getByText('Sample complete in this browser.')).toBeVisible()
  expect(writes).toEqual([])
  const isolated = await context.browser()!.newContext()
  const other = await isolated.newPage()
  await other.goto('http://127.0.0.1:5187/')
  await expect(other.getByRole('button', { name: 'Start local sample' })).toBeVisible()
  await isolated.close()
})

test('signed-in import keeps local progress on failure and confirms a retry', async ({ page }) => {
  const guestId = '12345678-1234-4234-8234-123456789abc'
  await page.addInitScript(({ guestId }) => {
    localStorage.setItem('pas:session', JSON.stringify({ token: 'test-token', user: { id: 'alice', login: 'alice', name: 'Alice' } }))
    localStorage.setItem('lango-learn:guest-sample:v1', JSON.stringify({ id: guestId, completedSteps: 2, savedAt: 1000 }))
  }, { guestId })
  let attempts = 0
  await page.route('https://api.proappstore.online/**', async route => {
    const url = route.request().url()
    if (url.endsWith('/actions/import_guest_lesson')) {
      attempts++
      await route.fulfill({ status: attempts === 1 ? 503 : 200, contentType: 'application/json', body: attempts === 1 ? '{"error":"temporary"}' : '{"results":[]}' })
    } else if (url.endsWith('/actions/get_guest_import_receipt')) {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ rows: [{ id: guestId, completed_steps: 2, outcome: 'imported' }] }) })
    } else {
      await route.fulfill({ status: 200, contentType: 'application/json', body: '{}' })
    }
  })
  await page.goto('/')
  const button = page.getByRole('button', { name: 'Save sample to my account' })
  await expect(button).toBeVisible()
  await button.click()
  await expect(page.getByText('The import could not be confirmed.')).toBeVisible()
  expect(await page.evaluate(() => JSON.parse(localStorage.getItem('lango-learn:guest-sample:v1')!).claimedBy)).toBeUndefined()
  await button.click()
  await expect(page.getByText('Saved 2 of 2 sample steps to your account.')).toBeVisible()
  expect(attempts).toBe(2)
  expect(await page.evaluate(() => JSON.parse(localStorage.getItem('lango-learn:guest-sample:v1')!).claimedBy)).toBe('alice')
})
