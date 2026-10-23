import { expect, test } from '@playwright/test'
import { execFileSync } from 'node:child_process'
import { mkdtempSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { pathToFileURL } from 'node:url'

test('local author preview shows exact scoring, feedback, audio fallback and small layout', async ({ page }) => {
  const output = mkdtempSync(join(tmpdir(), 'lango-author-e2e-'))
  execFileSync('python3', ['scripts/build_author_preview.py', 'content/fixtures/synthetic-package.json', '--output', output])
  await page.goto(pathToFileURL(join(output, 'index.html')).href)
  await expect(page.getByRole('heading', { name: 'Lango Learn · author preview' })).toBeVisible()
  await expect(page.getByText('Audio file unavailable in this preview.')).toBeVisible()
  await expect(page.getByText('Transcript: Synthetic audio')).toBeVisible()
  await page.getByRole('button', { name: 'Select one answer: sample-c' }).click()
  await expect(page.getByRole('status').getByText('Response not accepted.')).toBeVisible()
  await expect(page.getByText('Expected: sample-a')).toBeVisible()
  await page.getByRole('button', { name: 'Show hint' }).click()
  await expect(page.getByText('Choose the first sample')).toBeVisible()
  await page.getByRole('button', { name: 'Select one answer: sample-a' }).click()
  await expect(page.getByRole('status').getByText('Accepted response.')).toBeVisible()
  await page.getByRole('button', { name: 'Select one answer: sample-b' }).click()
  await expect(page.getByText('Accepted variant: Synthetic regional variant')).toBeVisible()
  await page.setViewportSize({ width: 320, height: 640 })
  const widths = await page.evaluate(() => ({ scroll: document.documentElement.scrollWidth, client: document.documentElement.clientWidth }))
  expect(widths.scroll).toBeLessThanOrEqual(widths.client)
})
