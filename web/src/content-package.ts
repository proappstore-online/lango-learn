/** Authoring snapshot v1. Runtime validation is performed by
 * scripts/validate_content_package.py before import or publication. */
export type LocaleTag = string
export type ContentId = string

export interface ContentPrompt {
  text: string
  locale: LocaleTag
  accessibleName: string
}

export interface ContentResponse {
  text: string
  locale: LocaleTag
}

export interface AcceptedVariant extends ContentResponse {
  reason: string
}

export interface ContentProvenance {
  type: 'original_lango'
  creator: string
  source: string
  rightsOwner: string
}

export interface AssetOrigin {
  type: 'original_lango'
  creator: string
  source: string
}

export interface AssetRights {
  owner: string
  licence: 'owned-original'
  territories: string[]
  attribution: string
  expiresOn: string | null
  replacement: string
}

export interface AssetAccessibility {
  altText: string | null
  decorative: boolean
  transcript: string | null
  nonAudioAlternative: boolean
}

interface BaseAsset {
  id: ContentId
  byteSize: number
  storageKey: string
  origin: AssetOrigin
  rights: AssetRights
  accessibility: AssetAccessibility
}

export interface ImageAsset extends BaseAsset {
  mimeType: 'image/png' | 'image/jpeg' | 'image/webp'
  durationSeconds?: never
  locale?: never
  accent?: never
}

export interface AudioAsset extends BaseAsset {
  mimeType: 'audio/mpeg' | 'audio/mp4' | 'audio/ogg'
  durationSeconds: number
  locale: LocaleTag
  accent: string
}

export type ContentAsset = ImageAsset | AudioAsset

export interface ContentExercise {
  id: ContentId
  position: number
  kind: 'recognition' | 'construction' | 'typed-recall' | 'listening'
  objectiveIds: ContentId[]
  prompt: ContentPrompt
  response: ContentResponse
  variants: AcceptedVariant[]
  hint: string
  explanation: string
  distractors: string[]
  mediaAssetIds: ContentId[]
  regionLocales: LocaleTag[]
  provenance: ContentProvenance
}

export interface ContentLesson {
  id: ContentId
  exercises: ContentExercise[]
}

export interface ContentObjective {
  id: ContentId
  locale: LocaleTag
}

export interface ContentPackage {
  schemaVersion: 1
  packageVersion: string
  courseVersionId: string
  sourceLocale: LocaleTag
  targetLocale: LocaleTag
  regionalLocales: LocaleTag[]
  objectives: ContentObjective[]
  assets: ContentAsset[]
  lessons: ContentLesson[]
}
