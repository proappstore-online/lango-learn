import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'
import { contractPath, validateLanguageCapabilities } from '../scripts/check_language_capabilities.mjs'

const contract = JSON.parse(readFileSync(contractPath, 'utf8'))
const copy = () => structuredClone(contract)

test('every profile has all nine capability fixtures and a conservative default', () => {
  assert.deepEqual(validateLanguageCapabilities(contract), [])
  assert.equal(contract.profiles.length, 4)
  assert.equal(contract.fixtures.length, 9 * contract.profiles.length)
  for (const fixture of contract.fixtures) {
    if (fixture.expectation === 'distinct') {
      assert.notEqual(fixture.left.normalize('NFC'), fixture.right.normalize('NFC'), `${fixture.tag}/${fixture.feature}`)
    }
  }
})

test('unsafe default equivalence and missing fixtures fail validation', () => {
  const unsafe = copy()
  unsafe.evaluationDefaults.diacriticRemoval = true
  assert.match(validateLanguageCapabilities(unsafe).join('\n'), /diacriticRemoval/)

  const missing = copy()
  missing.fixtures.pop()
  assert.match(validateLanguageCapabilities(missing).join('\n'), /missing ar-SA\/doNotNormalise/)
})

test('RTL metadata and do-not-normalise cases cannot silently weaken', () => {
  const wrongDirection = copy()
  wrongDirection.profiles.find((profile) => profile.tag === 'ar-SA').script.direction = 'ltr'
  assert.match(validateLanguageCapabilities(wrongDirection).join('\n'), /Arabic script must be rtl/)

  const unsafeCase = copy()
  unsafeCase.fixtures.find((fixture) => fixture.tag === 'es-ES' && fixture.feature === 'doNotNormalise').expectation = 'explicit_variant_only'
  assert.match(validateLanguageCapabilities(unsafeCase).join('\n'), /do-not-normalise must be distinct/)
})
