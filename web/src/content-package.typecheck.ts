import type { ContentAsset, ContentExercise, ContentPackage, ContentProvenance } from './content-package'

// Compiled by the normal typecheck. The runtime fixture is checked by the
// Python validator; these assertions keep the author-facing TS contract strict.
export const validExercise = {
  id: 'synthetic-exercise', position: 0, kind: 'recognition',
  objectiveIds: ['synthetic-objective'],
  prompt: { text: 'Select a sample', locale: 'en-US', accessibleName: 'Select one answer' },
  response: { text: 'sample-a', locale: 'es-ES' },
  variants: [{ text: 'sample-b', locale: 'es-MX', reason: 'regional form' }],
  hint: 'Choose a sample', explanation: 'Synthetic only', distractors: ['sample-c'],
  mediaAssetIds: ['synthetic-audio'], regionLocales: ['es-ES'],
  provenance: { type: 'original_lango', creator: 'Lango Learn', source: 'synthetic fixture', rightsOwner: 'Lango Learn' },
} satisfies ContentExercise

export const validAsset = {
  id: 'synthetic-audio', mimeType: 'audio/mpeg', byteSize: 1000,
  durationSeconds: 2, locale: 'es-ES', accent: 'synthetic voice',
  storageKey: 'draft/synthetic.mp3',
  origin: { type: 'original_lango', creator: 'Lango Learn', source: 'synthetic fixture' },
  rights: { owner: 'Lango Learn', licence: 'owned-original', territories: ['AU'],
    attribution: 'Lango Learn', expiresOn: null, replacement: 'replace fixture' },
  accessibility: { altText: null, decorative: false, transcript: 'Synthetic audio', nonAudioAlternative: true },
} satisfies ContentAsset

export const validPackage = {
  schemaVersion: 1, packageVersion: 'synthetic-1', courseVersionId: 'synthetic-version',
  sourceLocale: 'en-US', targetLocale: 'es-ES', regionalLocales: ['es-MX'],
  objectives: [{ id: 'synthetic-objective', locale: 'es-ES' }],
  assets: [validAsset], lessons: [{ id: 'synthetic-lesson', exercises: [validExercise] }],
} satisfies ContentPackage

// @ts-expect-error provenance cannot omit the rights owner
export const incompleteProvenance: ContentProvenance = { type: 'original_lango', creator: 'x', source: 'x' }
// @ts-expect-error third-party assets cannot enter the original-only package
export const thirdPartyAsset: ContentAsset = { ...validAsset, origin: { ...validAsset.origin, type: 'external' } }
// @ts-expect-error audio requires its accessible transcript metadata
export const incompleteAudio: ContentAsset = { ...validAsset, accessibility: { decorative: false, altText: null, nonAudioAlternative: true } }
