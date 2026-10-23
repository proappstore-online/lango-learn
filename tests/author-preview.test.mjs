import assert from 'node:assert/strict'
import { execFileSync, spawnSync } from 'node:child_process'
import { mkdtempSync, readFileSync, writeFileSync, mkdirSync, symlinkSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import test from 'node:test'

const script = 'scripts/build_author_preview.py'
const fixture = 'content/fixtures/synthetic-package.json'

test('builds a local preview only from a validated package', () => {
  const root = mkdtempSync(join(tmpdir(), 'lango-preview-'))
  const output = join(root, 'preview')
  execFileSync('python3', [script, fixture, '--output', output])
  const html = readFileSync(join(output, 'index.html'), 'utf8')
  assert.match(html, /Synthetic regional variant/)
  assert.match(html, /Audio file unavailable/)
  const invalid = JSON.parse(readFileSync(fixture, 'utf8'))
  invalid.lessons[0].exercises[0].position = 2
  writeFileSync(join(root, 'invalid.json'), JSON.stringify(invalid))
  const failed = spawnSync('python3', [script, join(root, 'invalid.json'), '--output', join(root, 'invalid-preview')], { encoding: 'utf8' })
  assert.equal(failed.status, 1)
  assert.match(failed.stderr, /contiguous/)
})

test('media must exist under the private root with matching size', () => {
  const root = mkdtempSync(join(tmpdir(), 'lango-preview-media-'))
  const media = join(root, 'media')
  mkdirSync(join(media, 'draft'), { recursive: true })
  writeFileSync(join(media, 'draft/synthetic-audio.mp3'), Buffer.alloc(1000))
  execFileSync('python3', [script, fixture, '--output', join(root, 'preview'), '--media-dir', media])
  assert.equal(readFileSync(join(root, 'preview/media/synthetic-audio.mp3')).length, 1000)
  writeFileSync(join(media, 'draft/synthetic-audio.mp3'), Buffer.alloc(3))
  const failed = spawnSync('python3', [script, fixture, '--output', join(root, 'wrong'), '--media-dir', media], { encoding: 'utf8' })
  assert.equal(failed.status, 1)
  assert.match(failed.stderr, /byteSize/)
  symlinkSync(media, join(root, 'linked-output'))
  const linked = spawnSync('python3', [script, fixture, '--output', join(root, 'linked-output')], { encoding: 'utf8' })
  assert.equal(linked.status, 1)
  assert.match(linked.stderr, /symbolic links/)
})
