import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

const features = [
  'tokenisation', 'morphology', 'wordOrder', 'punctuation', 'diacritics',
  'transliteration', 'regionalVariants', 'script', 'doNotNormalise',
]
const safeDefaults = [
  'caseFolding', 'whitespaceCollapse', 'punctuationRemoval', 'diacriticRemoval',
  'transliteration', 'regionalSubstitution', 'morphologicalExpansion', 'wordReordering',
]
const strategies = {
  tokenisation: 'reviewed_boundaries', morphology: 'explicit_forms',
  wordOrder: 'ordered_tokens', punctuation: 'content_defined',
  diacritics: 'preserve', transliteration: 'explicit_variants_only',
  regionalVariants: 'explicit_variants_only',
}

export function validateLanguageCapabilities(contract) {
  const errors = []
  const fail = (path, message) => errors.push(`${path}: ${message}`)
  const object = (value) => value !== null && typeof value === 'object' && !Array.isArray(value)
  if (!object(contract)) return ['contract: expected object']
  if (contract.schemaVersion !== 1) fail('schemaVersion', 'expected 1')
  if (contract.status !== 'illustrative_not_launched') fail('status', 'must not claim a launched language')
  if (!object(contract.evaluationDefaults)) {
    fail('evaluationDefaults', 'expected object')
  } else {
    if (contract.evaluationDefaults.unicodeNormalization !== 'NFC') fail('evaluationDefaults.unicodeNormalization', 'expected NFC')
    for (const key of safeDefaults) {
      if (contract.evaluationDefaults[key] !== false) fail(`evaluationDefaults.${key}`, 'must default to false')
    }
  }
  if (!Array.isArray(contract.profiles) || contract.profiles.length === 0) {
    fail('profiles', 'expected nonempty array')
  }
  const tags = new Set()
  for (const [index, profile] of (Array.isArray(contract.profiles) ? contract.profiles : []).entries()) {
    const path = `profiles[${index}]`
    if (!object(profile)) { fail(path, 'expected object'); continue }
    if (typeof profile.tag !== 'string' || !/^[a-z]{2,3}-[A-Z]{2}$/.test(profile.tag) || !Intl.getCanonicalLocales(profile.tag).includes(profile.tag)) {
      fail(`${path}.tag`, 'expected canonical language-region tag')
    }
    if (tags.has(profile.tag)) fail(`${path}.tag`, 'duplicate tag')
    tags.add(profile.tag)
    if (!object(profile.script) || !/^[A-Z][a-z]{3}$/.test(profile.script.code ?? '') ||
      !['ltr', 'rtl'].includes(profile.script.direction) || !profile.script.input) {
      fail(`${path}.script`, 'expected ISO 15924 code, direction and input guidance')
    }
    if (profile.script?.code === 'Arab' && profile.script.direction !== 'rtl') fail(`${path}.script.direction`, 'Arabic script must be rtl')
    for (const [feature, strategy] of Object.entries(strategies)) {
      if (!object(profile[feature]) || profile[feature].strategy !== strategy ||
        typeof profile[feature].note !== 'string' || !profile[feature].note.trim()) {
        fail(`${path}.${feature}`, `expected ${strategy} and a note`)
      }
    }
    if (!Array.isArray(profile.regionalVariants?.tags) || profile.regionalVariants.tags.length === 0 ||
      profile.regionalVariants.tags.some((tag) => typeof tag !== 'string' || tag === profile.tag || !/^[a-z]{2,3}-[A-Z]{2}$/.test(tag))) {
      fail(`${path}.regionalVariants.tags`, 'expected distinct region tags')
    }
    if (!Array.isArray(profile.doNotNormalise) || profile.doNotNormalise.length === 0 ||
      profile.doNotNormalise.some((item) => typeof item !== 'string' || !item.trim())) {
      fail(`${path}.doNotNormalise`, 'expected explicit non-normalisation cases')
    }
  }
  if (!Array.isArray(contract.fixtures)) {
    fail('fixtures', 'expected array')
  } else {
    const coverage = new Set()
    for (const [index, fixture] of contract.fixtures.entries()) {
      const path = `fixtures[${index}]`
      if (!object(fixture)) { fail(path, 'expected object'); continue }
      if (!tags.has(fixture.tag)) fail(`${path}.tag`, 'unknown profile')
      if (!features.includes(fixture.feature)) fail(`${path}.feature`, 'unknown feature')
      if (typeof fixture.left !== 'string' || !fixture.left.trim() ||
        typeof fixture.right !== 'string' || !fixture.right.trim() || fixture.left === fixture.right) {
        fail(path, 'expected two different nonempty examples')
      }
      if (!['distinct', 'explicit_variant_only'].includes(fixture.expectation)) fail(`${path}.expectation`, 'unsafe expectation')
      if (fixture.feature === 'doNotNormalise' && fixture.expectation !== 'distinct') fail(`${path}.expectation`, 'do-not-normalise must be distinct')
      const key = `${fixture.tag}/${fixture.feature}`
      if (coverage.has(key)) fail(path, 'duplicate feature fixture')
      coverage.add(key)
    }
    for (const tag of tags) for (const feature of features) {
      if (!coverage.has(`${tag}/${feature}`)) fail('fixtures', `missing ${tag}/${feature}`)
    }
  }
  return errors
}

export const contractPath = fileURLToPath(new URL('../contracts/language-capabilities.json', import.meta.url))

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  const errors = validateLanguageCapabilities(JSON.parse(readFileSync(contractPath, 'utf8')))
  if (errors.length) {
    for (const error of errors) console.error(error)
    process.exitCode = 1
  } else {
    console.log('Language capability contract valid')
  }
}
