# Content package contract (LNG-033)

A package is a UTF-8 JSON snapshot for **one course version**. Run
`python3 scripts/validate_content_package.py path/to/package.json` before an
editor or import pipeline exists. Exit status 0 means the package passes the
structural checks; errors carry JSON paths. The committed example is synthetic
fixture data, not approved course content. Keep draft media in private storage;
`storageKey` is a relative private key, never a public URL or credential.
The matching TypeScript authoring shapes live in `web/src/content-package.ts`.
Type checking catches missing fields and invalid literal values for TS authors;
the Python validator remains the runtime gate for JSON input, text, references,
rights metadata, and contiguous sequence positions.

`schemaVersion` selects this contract; `packageVersion` and `courseVersionId`
identify the immutable content snapshot. `sourceLocale`, `targetLocale`, and
`regionalLocales` use canonical course-map locale tags. `objectives` lists
version-scoped graph node IDs; each exercise references one or more. The
validator checks package-local references, including media IDs, but an eventual
import must verify IDs and version membership against D1.

Each lesson has exercises at unique positions `0..n-1`. This order matches the
current learner checkpoint. The live `create_exercise` action now accepts only
the next position, and review submission rejects previously stored gaps.
Exercises declare prompt text, locale and accessible name; response text and
locale; explicit accepted variants with their regional locale and rationale;
hint, explanation, distractors, media references, and region applicability.
No implicit case, punctuation, diacritic, transliteration, or word-order
normalisation is inferred from variants. All text is plain text; HTML markup
and control characters fail validation. The later exercise contract owns
scoring semantics for each kind.

Media entries declare MIME, byte size, private key, and original creator/source.
Rights record owner, licence, territories, expiry, attribution, and replacement.
Until LNG-007 clears a broader rights policy, only `owned-original` assets and
`original_lango` text are valid. Images need alt text unless decorative. Audio
needs transcript, non-audio alternative, accent, locale, and duration. The
limits mirror `docs/config-contract.md`; they are package metadata checks, not
proof of actual file format, media contents, or legal ownership. The media
intake work must inspect real files before publication.

This validator is a pre-editor authoring gate. LNG-039 later adds release-wide
validation against stored graph, asset, and lifecycle state. A passing package
does not approve learning outcomes, rights, linguistic accuracy, accessibility
on devices, or a publication decision.
