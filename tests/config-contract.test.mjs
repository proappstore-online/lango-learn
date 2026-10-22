import assert from 'node:assert/strict'
import { execFileSync } from 'node:child_process'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'

const root = fileURLToPath(new URL('..', import.meta.url))
const tracked = execFileSync('git', ['ls-files', '-z'], { cwd: root }).toString().split('\0').filter(Boolean)

test('environment files are not tracked', () => {
  const environmentFiles = tracked.filter((path) => path.split('/').some((part) => /^\.env(?:\.|$)/.test(part)))
  assert.deepEqual(environmentFiles, [])
})

test('public source and build config use only reviewed public environment values', () => {
  const publicFiles = tracked.filter((path) =>
    /^(web|marketing)\/(src|public)\//.test(path) ||
    /^(web|marketing)\/(index\.html|vite\.config\.ts|astro\.config\.ts)$/.test(path) ||
    path === '.github/workflows/deploy.yml',
  )

  for (const path of publicFiles) {
    if (!/\.(?:ts|tsx|js|jsx|mjs|astro|html|yml)$/.test(path)) continue
    const source = readFileSync(resolve(root, path), 'utf8')
    const exposed = [...source.matchAll(/\b(?:VITE|PUBLIC)_[A-Z0-9_]+\b/g)].map((match) => match[0])
    for (const name of exposed) {
      assert.equal(name, 'VITE_COMMIT_SHA', `${path}: unreviewed public environment value ${name}`)
    }
    assert.doesNotMatch(source, /\b(?:import\.meta|process)\.env\s*(?:\.|\[)/, `${path}: environment read needs review`)
  }
})
