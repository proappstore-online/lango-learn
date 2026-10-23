import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { spawnSync } from 'node:child_process'
import test from 'node:test'

const fixture = JSON.parse(readFileSync(new URL('../content/fixtures/synthetic-package.json', import.meta.url)))
const check = (change) => {
  const value = structuredClone(fixture)
  change(value)
  const child = spawnSync('python3', ['-c', 'import json,sys; from scripts.validate_content_package import validate; print("\\n".join(validate(json.load(sys.stdin))))'], {
    input: JSON.stringify(value), encoding: 'utf8'
  })
  assert.equal(child.status, 0, child.stderr)
  return child.stdout.trim()
}

test('synthetic original content package validates', () => {
  assert.equal(check(() => {}), '')
})

test('exercise positions must be unique and contiguous from zero', () => {
  for (const position of [2, -1, 0.5]) {
    assert.match(check(p => { p.lessons[0].exercises[0].position = position }), /position/)
  }
  assert.match(check(p => { p.lessons[0].exercises.push({...p.lessons[0].exercises[0], id: 'second', position: 2}) }), /contiguous/)
})

test('response, variants, distractors, and references are checked', () => {
  assert.match(check(p => { p.lessons[0].exercises[0].distractors = ['sample-a'] }), /accepted response/)
  assert.match(check(p => { p.lessons[0].exercises[0].variants[0].text = 'sample-a' }), /duplicate accepted/)
  assert.match(check(p => { p.lessons[0].exercises[0].objectiveIds = ['missing'] }), /unknown objective/)
  assert.match(check(p => { p.lessons[0].exercises[0].mediaAssetIds = ['missing'] }), /unknown asset/)
})

test('rights, accessibility, regional, and markup failures are rejected', () => {
  assert.match(check(p => { p.assets[0].origin.type = 'external' }), /only original/)
  assert.match(check(p => { p.assets[0].rights.licence = 'unknown' }), /owned-original/)
  assert.match(check(p => { p.assets[0].rights.expiresOn = '2000-01-01' }), /expired/)
  assert.match(check(p => { p.assets[0].accessibility.transcript = '' }), /transcript/)
  assert.match(check(p => { p.lessons[0].exercises[0].regionLocales = ['fr-FR'] }), /outside the course/)
  assert.match(check(p => { p.lessons[0].exercises[0].prompt.text = '<script>x</script>' }), /markup/)
})
