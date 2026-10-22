// LNG-013: mobile/accessibility baseline automated checks. Full device and screen-reader verification requires manual review.
import { expect, test, type Page } from '@playwright/test'

async function openShell(page: Page) {
  await page.goto('/')
  await expect(page.getByRole('button', { name: 'Sign in with GitHub' })).toBeVisible()
}

async function expectNoHorizontalScroll(page: Page) {
  const widths = await page.evaluate(() => {
    const client = document.documentElement.clientWidth
    const clipped = [...document.querySelectorAll('h1, h2, p, button, a, input, select, textarea')]
      .filter((element) => {
        const style = getComputedStyle(element)
        return style.display !== 'none' && style.visibility !== 'hidden' && element.getClientRects().length > 0
      })
      .filter((element) => {
        const bounds = element.getBoundingClientRect()
        return bounds.left < -1 || bounds.right > client + 1
      })
      .map((element) => element.tagName.toLowerCase())
    return { scroll: document.documentElement.scrollWidth, client, clipped }
  })
  expect(widths.scroll).toBeLessThanOrEqual(widths.client)
  expect(widths.clipped).toEqual([])
}

async function expectTabReachesAppContent(page: Page) {
  let reached = false
  for (let index = 0; index < 10; index += 1) {
    await page.keyboard.press('Tab')
    reached = await page.evaluate(() => {
      const active = document.activeElement
      if (!(active instanceof HTMLElement)) return false
      const label = active.getAttribute('aria-label') || active.innerText || active.getAttribute('title')
      return Boolean(label?.trim() && active.closest('main, #root'))
    })
    if (reached) break
  }
  expect(reached).toBe(true)
}

test.describe('375px mobile baseline', () => {
  test.use({ viewport: { width: 375, height: 812 } })

  test('has no horizontal document scroll', async ({ page }) => {
    await openShell(page)
    await expectNoHorizontalScroll(page)
  })

  test('visible controls have 44px touch targets', async ({ page }) => {
    await openShell(page)
    const undersized = await page.locator('button, a, input, select, textarea').evaluateAll((elements) =>
      elements.flatMap((element) => {
        if (!(element instanceof HTMLElement) || element.closest('[aria-hidden="true"]')) return []
        const style = getComputedStyle(element)
        if (style.display === 'none' || style.visibility === 'hidden' || element.getClientRects().length === 0) return []
        const bounds = element.getBoundingClientRect()
        return bounds.width >= 44 && bounds.height >= 44
          ? []
          : [`${element.tagName.toLowerCase()} ${element.textContent?.trim() || element.getAttribute('aria-label') || ''}: ${bounds.width}×${bounds.height}`]
      }),
    )
    expect(undersized).toEqual([])
  })

  test('keyboard focus has a visible indicator', async ({ page }) => {
    await openShell(page)
    await page.keyboard.press('Tab')
    const indicator = await page.evaluate(() => {
      const active = document.activeElement
      if (!(active instanceof HTMLElement) || active === document.body) return false
      const style = getComputedStyle(active)
      return (style.outlineStyle !== 'none' && parseFloat(style.outlineWidth) > 0) || style.boxShadow !== 'none'
    })
    expect(indicator).toBe(true)
  })

  test('reduces interactive transitions on request', async ({ page }) => {
    await page.emulateMedia({ reducedMotion: 'reduce' })
    await openShell(page)
    const durations = await page.getByRole('button', { name: 'Sign in with GitHub' }).evaluate((button) =>
      getComputedStyle(button).transitionDuration.split(',').map((value) => value.trim()),
    )
    expect(durations.every((value) => value.endsWith('ms')
      ? parseFloat(value) <= 10
      : parseFloat(value) <= 0.01)).toBe(true)
  })

  test('Tab reaches labeled app content', async ({ page }) => {
    await openShell(page)
    await expectTabReachesAppContent(page)
  })
})

test.describe('1280px desktop baseline', () => {
  test.use({ viewport: { width: 1280, height: 800 } })

  test('has no horizontal document scroll', async ({ page }) => {
    await openShell(page)
    await expectNoHorizontalScroll(page)
  })

  test('heading and paragraph tokens meet basic contrast in light and dark themes', async ({ page }) => {
    await openShell(page)
    // Token comparison is a smoke check; full WCAG contrast needs a dedicated audit and manual review.
    for (const theme of ['light', 'dark']) {
      const ratios = await page.evaluate((selectedTheme) => {
        document.documentElement.dataset.theme = selectedTheme
        const root = getComputedStyle(document.documentElement)
        const heading = document.querySelector('h1')
        const paragraph = document.querySelector('p')
        const paper = root.getPropertyValue('--paper').trim()
        const rgb = (value: string) => {
          if (value.startsWith('#')) return [1, 3, 5].map((index) => parseInt(value.slice(index, index + 2), 16))
          return (value.match(/[\d.]+/g) || []).slice(0, 3).map(Number)
        }
        const luminance = (value: string) => rgb(value)
          .map((channel) => channel / 255)
          .map((channel) => channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4)
          .reduce((sum, channel, index) => sum + channel * [0.2126, 0.7152, 0.0722][index], 0)
        const ratio = (foreground: string) => {
          const values = [luminance(foreground), luminance(paper)].sort((a, b) => b - a)
          return (values[0] + 0.05) / (values[1] + 0.05)
        }
        return {
          heading: heading ? ratio(getComputedStyle(heading).color) : 0,
          paragraph: paragraph ? ratio(getComputedStyle(paragraph).color) : 0,
        }
      }, theme)
      expect(ratios.heading, `${theme} heading`).toBeGreaterThanOrEqual(4.5)
      expect(ratios.paragraph, `${theme} paragraph`).toBeGreaterThanOrEqual(4.5)
    }
  })

  test('Tab reaches labeled app content', async ({ page }) => {
    await openShell(page)
    await expectTabReachesAppContent(page)
  })
})
