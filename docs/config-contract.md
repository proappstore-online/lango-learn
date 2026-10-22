# Lango Learn environment and configuration contract

This records the configuration rules for the current shell and the defaults that
new course features must adopt. [Architecture decisions](architecture.md) own
the client/server and authorization boundaries; the [planning backlog](comprehensive-epics-and-issues.md)
owns the later implementation tickets. There is no runtime flag service or media
upload path in the checked-in app today.

## Environments and trust boundary

| Environment | Configuration source | Allowed contents |
| --- | --- | --- |
| Local | Gitignored `.env.local` for local public build values; developer's PAS session for authenticated calls | Test identifiers and local settings. Do not put production credentials in the Vite environment. |
| CI | Repository variables for public build values; GitHub OIDC for the deploy workflow | `VITE_COMMIT_SHA` is the only public build variable currently used. OIDC credentials are short lived and stay in the deploy job. |
| Hosted app | Built `web/dist` plus PAS authenticated actions and private R2 | The browser receives only public identifiers and presentation data. D1, authorization, private media, and any paid API access remain on the platform side. |

Vite exposes `VITE_*` values to the browser bundle. Treat **all** client source,
`web/public`, `marketing/public`, PWA caches, and build-time substitutions as
public. Never put an API key, token, password, signing key, R2 credential, or
provider secret in a `VITE_*`/`PUBLIC_*` variable, client file, or public asset.
Do not commit any `.env*` file. Use PAS server-side capabilities such as
`app.proxy` for provider credentials; keep private media in private R2, accessed
through an authorized server path. A client flag, hidden UI, or unguessable URL
never grants access. The current `mcp.json` actions require authentication and
scope learner rows with `:__user_id`.

## Feature flags and safe defaults

No feature flag is evaluated by the current shell. Until LNG-121 supplies an
audited server-side flag service, **all unreleased features are off**. A missing,
invalid, or unavailable flag resolves to off; local development may opt in only
with test data. The first flag registry should use these names and defaults:

| Flag | Default | Controls |
| --- | --- | --- |
| `lessons_enabled` | off | Learner access to a reviewed, published course release. |
| `audio_enabled` | off | Lesson audio after licensed media and a non-audio route are ready. |
| `offline_packs_enabled` | off | Downloaded versioned course packs. |
| `notifications_enabled` | off | Opt-in learning reminders after preference controls exist. |
| `experiments_enabled` | off | Reviewed, bounded learner-benefit experiments. |
| `social_enabled` | off | Post-MVP social features after moderation and consent gates. |
| `ai_practice_enabled` | off | Post-MVP AI practice after privacy and safety review. |
| `billing_enabled` | off | Post-MVP optional enrichment after entitlement review. |

When implemented, evaluate release flags on the server for global-off, staff,
and bounded cohorts; record assignment and exposure as LNG-121 requires. Publish
one approved immutable course release before enabling lessons. Flags can reduce
exposure but cannot bypass PAS roles, `:__user_id` SQL scoping, publication
checks, consent, or entitlements. No flag may remove core lessons, explanations,
accessibility accommodations, or review from the free path. A global off must
be available without rebuilding the browser bundle.

## Media limits

These are app-level maximums for **future** media intake, not limits enforced by
the current shell. LNG-070 must enforce them on the server after inspecting the
actual file, with client checks only as early feedback. Platform limits can be
stricter. Reject unknown formats and files over the limit; do not silently
transcode or publish a draft.

| Asset | Accepted format | Maximum per file | Additional requirement |
| --- | --- | --- | --- |
| Lesson illustration | PNG, JPEG, or WebP | 5 MiB | Alt text or an explicit decorative designation; rights and provenance. |
| Lesson audio | MP3, AAC (`audio/mp4`), or Ogg Opus | 10 MiB and 120 seconds | Transcript or equivalent non-audio exercise route; language/accent and rights metadata. |
| Learner recording | None in R0–R3 | 0 | Disabled until LNG-140 defines consent, retention, deletion, and size/duration limits. |

MIME, byte size, decoded duration, rights, transcript/accessibility metadata,
and release state must be checked before publication. Drafts and private media
remain private; public, versioned assets must belong to an approved release.
The current icons and Open Graph image are static branding assets, not lesson
uploads. The PWA's 10 MiB cache entry ceiling in `web/vite.config.ts` is a
cache setting, **not** an upload allowance or proof that private media is safe
to cache.

## Supported browsers and verification

Target the current and immediately previous stable major releases of Chrome,
Edge, Firefox, and Safari on desktop, plus Safari on supported iOS and Chrome
on supported Android. The minimum layout width is 375 CSS pixels; keyboard,
focus, reduced motion, and touch targets follow the
[accessibility baseline](accessibility-manual-review.md). Do not claim older
browser or offline lesson support without a separate release test.

CI currently runs Playwright in desktop Chromium and Chromium with an iPhone SE
device profile. The latter emulates a mobile viewport and input, **not** Safari
or a physical iPhone. Firefox, WebKit/Safari, Android Chrome, and physical-device
checks remain release verification work; the manual checklist records that gap.
New browser APIs need a fallback or an explicit support decision before use.

## Checks

`pnpm test` includes `tests/config-contract.test.mjs`. It rejects tracked
`.env*` files and unreviewed public environment reads or build substitutions.
That check cannot detect every hard-coded credential or enforce future upload
limits; those require code-path validation and review when the features land.
