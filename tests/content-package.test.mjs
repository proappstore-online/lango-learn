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

test('all required exercise content and provenance fields are checked', () => {
  const invalid = [
    [p => { p.lessons[0].exercises[0].prompt.accessibleName = '' }, /accessibleName/],
    [p => { p.lessons[0].exercises[0].response.text = '' }, /response.text/],
    [p => { p.lessons[0].exercises[0].variants[0].reason = '' }, /variants\[0\].reason/],
    [p => { p.lessons[0].exercises[0].hint = '' }, /hint/],
    [p => { p.lessons[0].exercises[0].explanation = '' }, /explanation/],
    [p => { p.lessons[0].exercises[0].distractors = [] }, /recognition needs distractors/],
    [p => { p.lessons[0].exercises[0].provenance.rightsOwner = '' }, /rightsOwner/],
    [p => { p.lessons[0].exercises[0].provenance.type = 'external' }, /only original/],
    [p => { p.assets[0].rights.owner = '' }, /rights.owner/],
    [p => { p.assets[0].origin.source = '' }, /origin.source/],
    [p => { p.assets[0].accessibility.nonAudioAlternative = false }, /nonAudioAlternative/],
    [p => { p.assets[0].mimeType = {} }, /mimeType/],
  ]
  for (const [change, expected] of invalid) assert.match(check(change), expected)
})

test('image metadata needs an accessible description unless decorative', () => {
  const asImage = p => {
    const asset = p.assets[0]
    asset.mimeType = 'image/png'
    delete asset.durationSeconds
    delete asset.locale
    delete asset.accent
    asset.accessibility.transcript = null
    asset.accessibility.altText = 'Synthetic image'
  }
  assert.equal(check(asImage), '')
  assert.match(check(p => { asImage(p); p.assets[0].accessibility.altText = null }), /altText/)
  assert.equal(check(p => { asImage(p); p.assets[0].accessibility.decorative = true; p.assets[0].accessibility.altText = null }), '')
  assert.match(check(p => { asImage(p); p.assets[0].accessibility.transcript = 'wrong field' }), /transcript/)
})
