import { expect, test } from '@playwright/test'
import { execFileSync } from 'node:child_process'
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
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
  await expect(page.getByRole('status').getByText('Author check: not accepted by package.')).toBeVisible()
  await expect(page.getByText('Expected: sample-a')).toBeVisible()
  await expect(page.getByText('Current learner result: pending_evaluation (ungraded).')).toBeVisible()
  await page.getByRole('button', { name: 'Show hint' }).click()
  await expect(page.getByText('Choose the first sample')).toBeVisible()
  await page.getByRole('button', { name: 'Select one answer: sample-a' }).click()
  await expect(page.getByRole('status').getByText('Author check: accepted by package.')).toBeVisible()
  await page.getByRole('button', { name: 'Select one answer: sample-b' }).click()
  await expect(page.getByText('Accepted variant: Synthetic regional variant')).toBeVisible()
  await page.setViewportSize({ width: 320, height: 640 })
  const widths = await page.evaluate(() => ({ scroll: document.documentElement.scrollWidth, client: document.documentElement.clientWidth }))
  expect(widths.scroll).toBeLessThanOrEqual(widths.client)
  const choices = await page.getByRole('group', { name: 'Select one answer' }).getByRole('button').evaluateAll(buttons => buttons.map(button => button.getBoundingClientRect().height))
  expect(choices.every(height => height >= 44)).toBe(true)
})

test('local media controls and typed input retain accessible names', async ({ page }) => {
  const root = mkdtempSync(join(tmpdir(), 'lango-author-media-e2e-'))
  const media = join(root, 'media')
  mkdirSync(join(media, 'draft'), { recursive: true })
  writeFileSync(join(media, 'draft/synthetic-audio.mp3'), Buffer.alloc(1000))
  const pkg = JSON.parse(readFileSync('content/fixtures/synthetic-package.json', 'utf8'))
  const second = structuredClone(pkg.lessons[0].exercises[0])
  second.id = 'synthetic-second'
  second.position = 1
  second.kind = 'typed-recall'
  second.prompt.accessibleName = 'Type the sample response'
  second.mediaAssetIds = []
  pkg.lessons[0].exercises.push(second)
  const packagePath = join(root, 'package.json')
  writeFileSync(packagePath, JSON.stringify(pkg))
  const output = join(root, 'preview')
  execFileSync('python3', ['scripts/build_author_preview.py', packagePath, '--output', output, '--media-dir', media])
  await page.goto(pathToFileURL(join(output, 'index.html')).href)
  const audio = page.getByLabel('Play Synthetic audio')
  await expect(audio).toBeVisible()
  await expect(audio.locator('source')).toHaveAttribute('src', 'media/synthetic-audio.mp3')
  await audio.dispatchEvent('error')
  await expect(page.getByText('Audio could not be played. Use the transcript below.')).toBeVisible()
  await page.getByRole('button', { name: 'Next' }).click()
  await expect(page.getByRole('textbox', { name: 'Type the sample response' })).toBeVisible()
  await page.getByRole('textbox', { name: 'Type the sample response' }).fill('sample-b')
  await page.getByRole('button', { name: 'Check response' }).click()
  await expect(page.getByText('Accepted variant: Synthetic regional variant')).toBeVisible()
})
