import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'

const root = fileURLToPath(new URL('..', import.meta.url))
const read = (path) => readFileSync(resolve(root, path), 'utf8')

test('Lango Learn uses independently branded shell controls', () => {
  const app = read('web/src/App.tsx')

  assert.match(app, /<ProShell app=\{app\} appName="Lango Learn" nav=\{NAV\} branding="app">/)
  assert.doesNotMatch(app, /Built for ProAppStore|href="https:\/\/proappstore\.online"/)
})

test('Lango Learn public metadata and manifest use its own brand', () => {
  const html = read('web/index.html')
  const vite = read('web/vite.config.ts')

  assert.match(html, /<title>Lango Learn<\/title>/)
  assert.match(html, /content="Lango Learn is preparing original lessons for thoughtful language practice\."/)
  assert.doesNotMatch(html, /ProAppStore/)
  assert.match(vite, /name: 'Lango Learn'/)
  assert.match(vite, /description: 'Original lessons for thoughtful language practice are in preparation\.'/)
  assert.doesNotMatch(vite, /ProAppStore/)
})

test('compliance does not require a public platform link', () => {
  const workflow = read('.github/workflows/compliance.yml')

  assert.doesNotMatch(workflow, /ProAppStore link/)
  assert.doesNotMatch(workflow, /grep -r "proappstore\.online" web\/src/)
})
