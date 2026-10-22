import { expect, test } from '@playwright/test'

test('home presents the branded sign-in entry', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Lango Learn', exact: true })).toBeVisible()
  await expect(page.getByText('Sign in to continue.')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Sign in with GitHub' })).toBeVisible()
})

test('about route keeps the same sign-in boundary', async ({ page }) => {
  await page.goto('/about')
  await expect(page).toHaveURL(/\/about$/)
  await expect(page.getByRole('heading', { name: 'Lango Learn', exact: true })).toBeVisible()
  await expect(page.getByText('Sign in to continue.')).toBeVisible()
})
