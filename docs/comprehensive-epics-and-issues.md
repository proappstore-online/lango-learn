# Lango Learn comprehensive epics and issues

Status: planning baseline — 2026-10-20  
Inputs: official product research, community-risk review, curriculum/learning-science
review, PAS technical review, and a delivery red-team pass. Supporting sources are
retained in [research-duolingo-product.md](research-duolingo-product.md).

## Non-negotiable product decisions

- Build an original product. Do not copy another product's brand, course content,
  visual system, characters, audio, or interaction patterns.
- MVP is one declared source-language → target-language pair, an A0 to early-A1
  slice, and Latin script. A "language launch" means reviewed content and support,
  not a generated shell.
- Use CEFR as an alignment framework and Lango Learn-authored learner goals. Do not
  claim certification or copy/licence restricted ACTFL Can-Do wording.
- Completion, XP, streaks, and a lesson path are not proof of proficiency.
- Deterministic, reviewed, language-aware answer evaluation is the MVP authority.
  Generative AI is never the only judge or publisher of educational material.
- Core lessons, explanations, accessibility accommodations, and review are never
  paywalled or restricted after mistakes.
- No hearts/energy monetisation, shame-based streak loss, forced social activity,
  forced timers, ads inside lessons, or undisclosed behavioural tracking.
- PAS constraints: use the SDK/ProShell, additive D1 migrations, PAS app roles,
  authorization-enforced `mcp.json` actions, private R2 for private media, and no
  third-party analytics cookies/pixels.

## Release slices

| Slice | Outcome | Included epics |
| --- | --- | --- |
| R0 — design proof | An approved, testable course and system contract exist. | E00–E03 |
| R1 — private learning alpha | A signed-in learner can finish/resume original lessons and receive useful feedback. | E04–E08 |
| R2 — pilot-ready learning loop | Learners can use review, audio, goals, and a quality/support path safely. | E09–E12 |
| R3 — public MVP | Accessibility, privacy, release controls, monitoring, and incident response pass release gates. | E13–E15 |
| Post-MVP | Add rich practice only after evidence validates the core loop. | E16–E19 |

## E00 — product charter, learning claims, and measurement (R0)

| ID | Issue | Done when | Depends on |
| --- | --- | --- | --- |
| LNG-001 | Approve learner/product charter | Names course pair, age/region, A1 boundary, supported skills, exclusions, and no-certification claims. | — |
| LNG-002 | Define Lango Learn-owned learning outcomes | Each outcome is contextual, observable, source/target-language scoped, and has evidence requirements. | LNG-001 |
| LNG-003 | Establish framework/licensing policy | CEFR/ACTFL references, permitted wording, attribution/licences, and marketing review are recorded. | LNG-001 |
| LNG-004 | Define learning and safety metrics | Separates exposure, retention, outcome performance, engagement, support load, accessibility, and revenue; prohibits revenue-from-failure metrics. | LNG-001 |
| LNG-005 | Define event taxonomy | Documents lesson, answer, hint, review, report, notification, and failure events without raw answers/audio in general analytics. | LNG-004 |
| LNG-006 | Establish experiment ethics gate | Every experiment has learner-benefit hypothesis, guardrails, stop rule, owner, and rollback. | LNG-004 |
| LNG-007 | Clear brand and asset rights | Trademark/name review plus an asset register record owner, licence, territory, expiry, attribution, and replacement path for every shipped text, image, recording, TTS, and dictionary source. | LNG-001 |

## E01 — PAS foundation and engineering guardrails (R0)

| ID | Issue | Done when | Depends on |
| --- | --- | --- | --- |
| LNG-010 | Scaffold compliant PAS app | React/Vite/TS, SDK, ProShell, typecheck, build, `pas check`, and live smoke test pass. | PAS app ownership |
| LNG-011 | Record architecture decisions | Client/server boundaries, UUID/time/error/pagination conventions, content versions, and action naming are documented in [architecture.md](architecture.md). | LNG-010 |
| LNG-012 | Establish development quality gates | Lint, unit, migration, action-authorization, build, and Playwright jobs run on pull requests. | LNG-010 |
| LNG-013 | Establish mobile/accessibility baseline | 375px layout, 44px controls, focus, contrast, reduced motion, and no horizontal scroll have automated/manual checks. | LNG-010 |
| LNG-014 | Create environment/config contract | Feature flags, safe defaults, media limits, supported browsers, and no-client-secret rule are documented. | LNG-011 |
| LNG-015 | Define per-language capability rules | Tokenisation, morphology, word order, punctuation, diacritics, transliteration, regional variants, scripts/RTL, and explicit “do not normalise” cases have fixtures. | LNG-011 |

## E02 — data model, authorization, and identity (R0)

| ID | Issue | Done when | Depends on |
| --- | --- | --- | --- |
| LNG-020 | Create initial additive D1 migration | Models profiles/preferences, courses/versions, lessons/exercises, sessions/attempts, exposures/review, reports, releases, audit rows, and indexes. | LNG-011 |
| LNG-021 | Build scoped learner action surface | Bootstrap, next/resume lesson, submit/complete, review, preference, and report actions scope all data by `:__user_id`. | LNG-020 |
| LNG-022 | Build role-gated staff action surface | Author/review/publish/retire/report actions enforce PAS roles and write audit records. | LNG-020 |
| LNG-023 | Define account and guest behaviour | Local-only first lesson is honest; sign-in is required for durable data; import/migration is idempotent and conflict-aware. | LNG-020 |
| LNG-024 | Configure staff roles | `curriculum_editor`, `content_reviewer`, `support`, and `moderator` permissions are documented and independently enforced. | LNG-022 |
| LNG-025 | Test authorization and migration contracts | Tests prove cross-user reads/writes fail and real migrations/actions work for learner and every staff role. | LNG-021, LNG-022 |

## E03 — curriculum, authoring, and publication (R0)

| ID | Issue | Done when | Depends on |
| --- | --- | --- | --- |
| LNG-030 | Implement course-map schema | Source/target BCP-47 tags, region/script, course version, unit, lesson, prerequisite, and release state are representable. | LNG-020 |
| LNG-031 | Implement objective and knowledge graph | Objectives link to lexemes, phrases, grammar, pronunciation, register, confusables, and prerequisite relationships. | LNG-030, LNG-002 |
| LNG-032 | Create pilot course blueprint | A qualified curriculum lead limits novel material, sequences objectives, and defines input, production, and delayed review. | LNG-031 |
| LNG-033 | Build content package and validator | Prompt, response, variants, hint, explanation, distractors, media, licence/provenance, accessibility, and regional metadata validate before a full editor exists. | LNG-031, LNG-007 |
| LNG-034 | Build author preview then authoring workspace | Package preview reproduces learner scoring, feedback, audio, accessible names, and small-screen layout; a full authoring UI is only funded after pilot content proves the workflow. | LNG-033 |
| LNG-035 | Define course style guide | Dialect, register, transliteration, punctuation, inclusive language, translations, feedback tone, and audio conventions are approved. | LNG-032 |
| LNG-036 | Implement content lifecycle | Draft → linguistic review → pedagogical review → approved → published/retired is auditable; publishers cannot approve their own high-impact content. | LNG-033 |
| LNG-037 | Build publication/rollback | Releases point to immutable course versions; active sessions keep snapshots; rollback repoints safely without data loss. | LNG-036 |
| LNG-038 | Build bulk import/export dry run | Imports report row/field errors without partial publish; exports complete, provenance-preserving snapshots. | LNG-033 |
| LNG-039 | Validate content before release | Blocks orphaned objectives, missing media/alternatives, contradictory variants, unsafe markup, invalid prerequisites, and unlicensed assets. | LNG-033, LNG-036 |

## E04 — onboarding, placement, and learner control (R1)

| ID | Issue | Done when | Depends on |
| --- | --- | --- | --- |
| LNG-040 | Build course/language selection | Learner selects base/target language and applicable dialect/orthography, with a reversible change path. | LNG-030 |
| LNG-041 | Build intent-based onboarding | Optional goal/date, reason, skill comfort, and preferred mode all support Skip. | LNG-040 |
| LNG-042 | Build flexible daily plan | Minutes/lessons, days, timezone, reminder window, no-goal option, pause/vacation, and weekly view work. | LNG-041 |
| LNG-043 | Build placement item bank | Reviewed items sample prerequisites and recognition/production with objective/difficulty hypotheses. | LNG-031 |
| LNG-044 | Build conservative placement recommendation | Learner chooses start/diagnostic/restart; recommendation exposes confidence and can be overridden with no penalty. | LNG-043 |
| LNG-045 | Instrument placement validity | Records recommendation, choice, confirmation performance, and re-placement outcomes without retaining unneeded raw answers. | LNG-044, LNG-005 |
| LNG-046 | Complete first-session activation | First lesson explains review and feedback, summarizes learning, and asks notification consent only after learner value. | LNG-042, LNG-060 |

## E05 — lesson session, exercise runtime, and evaluation (R1)

| ID | Issue | Done when | Depends on |
| --- | --- | --- | --- |
| LNG-050 | Define exercise contract | Every template declares skill, prerequisite, input, accessibility alternate, authoritative evaluator, feedback, and fixtures. | LNG-033 |
| LNG-051 | Build resumable session service | Start/checkpoint/resume/complete are idempotent; a session records exact course/exercise version and sequence. | LNG-021, LNG-037 |
| LNG-052 | Ship recognition and contextual selection | Original accessible interactions render/evaluate with fixtures and content-defined distractors. | LNG-050, LNG-051 |
| LNG-053 | Ship word/phrase assembly | Keyboard/screen-reader alternative exists; order/token behavior is locale-aware. | LNG-050, LNG-051 |
| LNG-054 | Ship typed production and cloze | Grapheme/IME/paste/diacritic handling is correct; no Latin-only assumptions. | LNG-050, LNG-051 |
| LNG-055 | Ship listening-recognition runtime | Player/error states integrate with replay, speed, transcript policy, and non-audio alternative. | LNG-050, LNG-070 |
| LNG-056 | Implement deterministic evaluator | Per-language normalization uses LNG-015 rules; variants, partial-credit rules, error codes, and response contracts are server-authoritative and documented. | LNG-015, LNG-031, LNG-050 |
| LNG-057 | Build golden evaluator corpus | Accepted/rejected/partial/dialectal/typographical/script/accessibility cases run on every evaluator change. | LNG-056 |
| LNG-058 | Build answer-variant workflow | Editors add versioned variants with rationale/tests; learner reports enter review rather than silently fuzzy-matching answers. | LNG-056, LNG-036 |
| LNG-059 | Make completion/progression atomic | A replayed request cannot duplicate rewards/evidence; prerequisites use released rules only. | LNG-051, LNG-056 |

## E06 — feedback, explanations, and learner correction (R1)

| ID | Issue | Done when | Depends on |
| --- | --- | --- | --- |
| LNG-060 | Build error taxonomy | Vocabulary, grammar, order, spelling, listening, and format are distinguished only when confidence supports it; unknown stays uncertain. | LNG-056 |
| LNG-061 | Deliver immediate corrective feedback | Correct answer, concise respectful explanation, retry, and useful next action appear without blocking progress. | LNG-060 |
| LNG-062 | Implement layered hints | Concept cue, narrowed hint, and explicit reveal are tracked for adaptation but never punished. | LNG-050, LNG-060 |
| LNG-063 | Publish grammar/usage cards | Concepts have explanation, examples, limits, and links; they are reachable before/during/after an exercise. | LNG-031 |
| LNG-064 | Build “why this answer?” | Shows context-specific, source-grounded explanation; uncertain/AI-assisted text is labelled and reportable. | LNG-061, LNG-063 |
| LNG-065 | Build report and triage flow | Wrong answer, unnatural phrasing, audio, translation, explanation, and accessibility reports carry minimal contextual data to a staff queue. | LNG-022, LNG-061 |
| LNG-066 | Build learner mistake notebook | Learner can revisit/delete saved mistakes, explanations, and tags; there is no punitive cap. | LNG-061 |

## E07 — mastery, review, course map, and outcomes (R1–R2)

| ID | Issue | Done when | Depends on |
| --- | --- | --- | --- |
| LNG-070 | Build media asset management | MIME/duration/size/rights/transcript/accent metadata validate; drafts stay private; no client storage secret exists. | LNG-033 |
| LNG-071 | Record component evidence ledger | Attempts record item/skill/mode/result/error/timestamp/version/policy separately from completion/XP. | LNG-056 |
| LNG-072 | Build initial spaced-retrieval scheduler | Deterministic policy uses delayed active recall and varied context; each recommendation returns a learner/support explanation. | LNG-071 |
| LNG-073 | Build session assembler | Respects prerequisite, novel-material limit, objective coverage, due review, and exercise diversity; emits a selection trace. | LNG-032, LNG-072 |
| LNG-074 | Build Review hub | Due, mistakes, vocabulary, grammar, listening, and unit practice are user-selectable and never alter course unlock state accidentally. | LNG-066, LNG-072 |
| LNG-075 | Build course map and progress | Shows current/finished objectives, review load, upcoming work, and evidence level; never markets XP as proficiency. | LNG-071 |
| LNG-076 | Build contextual checkpoints | Each unit validates outcomes with varied integrated-context tasks, not a memorized item alone. | LNG-032, LNG-061 |
| LNG-077 | Build adaptation controls | Learner can pin/review, mark too easy/hard, reset placement, and report poor recommendations. | LNG-072, LNG-075 |

## E08 — PWA, offline use, and media performance (R2)

| ID | Issue | Done when | Depends on |
| --- | --- | --- | --- |
| LNG-080 | Deliver PWA app shell | Manifest, icons, service worker, offline page, update prompt, install, and HTTPS behavior pass on supported mobile browsers; this does not promise offline learning. | LNG-010 |
| LNG-081 | Add accessible audio player | Replay, speed, captions/transcript, keyboard, failure fallback, and a non-audio option work for every MVP listening item. | LNG-055, LNG-070 |
| LNG-082 | Establish media performance budget | Versioned URLs, lazy loading, limited preload, and graceful media failure prevent audio delaying lesson start. | LNG-070 |
| LNG-083 | Build versioned course packs | Signed-in learner downloads released content/audio, sees storage/clear controls, and never caches draft/private media publicly. | LNG-080, LNG-037 |
| LNG-084 | Build offline attempt outbox | Ordered, idempotent sync shows pending/failed state; changed or retired content cannot corrupt progress. | LNG-051, LNG-083 |
| LNG-085 | Test offline/update lifecycle | Tests cover cold offline launch, connection loss, duplicate sync, version update, cache clear, and logout. | LNG-084 |

## E09 — accessibility and healthy habit design (R2, release-critical)

| ID | Issue | Done when | Depends on |
| --- | --- | --- | --- |
| LNG-090 | Build accessible component catalogue | Semantic names/roles/states, focus, contrast, text scaling, reduced motion, and touch targets have automated checks. | LNG-013 |
| LNG-091 | Guarantee exercise accessibility parity | Core exercises are keyboard/VoiceOver/TalkBack usable, use target-language metadata, and offer non-drag/non-timed alternatives. | LNG-052–055, LNG-090 |
| LNG-092 | Add sensory/input accommodations | Captions, speed/replay, no-mic/no-audio paths, haptic/sound toggles, dyslexia-friendly settings, and motion controls work in lessons. | LNG-081, LNG-090 |
| LNG-093 | Establish untimed curriculum policy | Timers never gate progression; optional challenges disclose timing and preserve an unranked mode. | LNG-090 |
| LNG-094 | Run accessibility validation | CI blocks regressions; release evidence includes iOS/Android screen-reader tests and usability sessions with disabled learners. | LNG-091 |
| LNG-095 | Implement compassionate daily activity | Timezone/DST-safe daily goal separates current/longest habit from learning; missed days never delete course progress. | LNG-042, LNG-059 |
| LNG-096 | Build focus and game-mechanic controls | Learner can hide rewards/celebrations, animation, sound/haptics, feeds, and competitive prompts; only one optional interstitial between lessons. | LNG-090 |
| LNG-097 | Build weekly reflection/restart | Reports skill/time progress, lets learner lower/pause goals, and offers realistic restart—not catch-up pressure. | LNG-075, LNG-095 |

## E10 — notifications and respectful re-engagement (R2)

| ID | Issue | Done when | Depends on |
| --- | --- | --- | --- |
| LNG-100 | Build notification preference centre | Separate lesson/review/weekly/social/marketing toggles, quiet hours, pause, and withdrawal apply across channels. | LNG-042 |
| LNG-101 | Implement learner-owned schedule | Selected days/time, timezone-safe changes, no smart-timing default, and one learning notification/day cap work. | LNG-100 |
| LNG-102 | Create reviewed reminder catalogue | Copy is truthful/localised and excludes shame, fake friend activity, streak threats, and false urgency. | LNG-006, LNG-100 |
| LNG-103 | Build re-engagement decisioning | Uses plan/review/last engagement with frequency/holdout/unsubscribe guards; success measures next-week learning, not opens alone. | LNG-005, LNG-101 |
| LNG-104 | Add incident suppression/repair | Outage mode stops reminders and repairs daily activity only with auditable service evidence. | LNG-095, LNG-005 |

## E11 — privacy, safeguarding, support, and content operations (R2)

| ID | Issue | Done when | Depends on |
| --- | --- | --- | --- |
| LNG-110 | Create data inventory and consent map | Field, purpose, legal basis, retention, processor, sensitivity, backup expiry, and support-verification process are documented before collection. | LNG-020 |
| LNG-111 | Build privacy centre | Learner can change consent, export, delete/correct data, and see retention exceptions; deletion propagates to D1, private media, analytics identifiers, transcripts/recordings, support reports, and documented backup expiry—not just SDK KV. | LNG-110 |
| LNG-112 | Establish age/safeguarding policy | Supported ages/jurisdictions, DOB use, staff visibility, and future social/speech restrictions are approved before relevant launch. | LNG-110 |
| LNG-113 | Implement staff report operations | Reports are triaged/assigned/resolved/audited; urgent content can be quarantined or rolled back without direct DB access. | LNG-065, LNG-037 |
| LNG-114 | Write content health monitor | Flags abnormal errors/skips/reports without assuming learner error equals bad content; human review can reschedule affected learners. | LNG-005, LNG-113 |
| LNG-115 | Build support and remediation routes | Account, lesson, accessibility, privacy, and incident support flows include consented diagnostics, severity, owner, and response target. | LNG-111, LNG-113 |
| LNG-116 | Establish security release review | Authorization matrix, XSS/sanitisation, private-media, dependency/secret, rate-limit, and log-PII checks pass. | LNG-025, LNG-070 |

## E12 — observability, flags, release, and pilot (R2–R3)

| ID | Issue | Done when | Depends on |
| --- | --- | --- | --- |
| LNG-120 | Implement aggregate learning observability | Funnel, answer category, runtime/sync failure, review uptake, report rate, and notification events are dashboardable without raw sensitive content. | LNG-005 |
| LNG-121 | Build audited server-side flags | Flags support global off, staff, and bounded cohort; exposure/assignment audits exist; flags never bypass access control. | LNG-014 |
| LNG-122 | Define staged release/rollback playbook | Internal → limited cohort → public has owner, success/abort thresholds, version/build/flag record, release notes, and rollback action. | LNG-037, LNG-121 |
| LNG-123 | Run learning pilot | A small pilot tests stated contextual outcomes, answer quality, review uptake, accessibility, and support burden before public expansion. | LNG-076, LNG-094, LNG-115 |
| LNG-124 | Calibrate placement/review from evidence | Uses held-out data, subgroup checks, versioning, and rollback; cannot replace baseline until it beats agreed outcome measure. | LNG-045, LNG-072, LNG-123 |
| LNG-125 | Complete public-MVP gate | Deploy/PWA/offline/accessibility/privacy/security/support/monitoring/rollback evidence is signed by named owners. | LNG-085, LNG-094, LNG-111, LNG-116, LNG-123 |

## E13 — optional social learning (post-MVP)

| ID | Issue | Done when | Depends on |
| --- | --- | --- | --- |
| LNG-130 | Build private learner profile | Display name/avatar/progress sharing are granular; discovery is off by default. | LNG-112 |
| LNG-131 | Build mutual connections | Requests, removal, blocking, and no exposure of email/schedule/exact activity work. | LNG-130 |
| LNG-132 | Build cooperative weekly goal | Two consenting learners share aggregate bounded progress; either leaves; nudges require recipient opt-in. | LNG-131, LNG-095 |
| LNG-133 | Build moderation controls | Block/report/rate limits/no open DMs/moderation audit/age restrictions precede social release. | LNG-113, LNG-112 |
| LNG-134 | Validate optional ranking | Only after anti-cheat, moderation, transparent cohorts, and rank-less opt-out; course progression never depends on it. | LNG-120, LNG-133 |

## E14 — speech and AI practice (post-MVP)

| ID | Issue | Done when | Depends on |
| --- | --- | --- | --- |
| LNG-140 | Build speaking-capture foundation | Just-in-time consent, indicator, skip/no-audio route, fallible transcript, and no-default-retention policy exist. | LNG-092, LNG-111 |
| LNG-141 | Add validated pronunciation feedback | Low-confidence and dialect cases are handled; score never blocks progression; recordings/transcripts are deletable. | LNG-140, LNG-123 |
| LNG-142 | Establish AI provenance and draft-only policy | Human reviewer owns published content; sources/versions are recorded; AI cannot auto-publish. | LNG-036 |
| LNG-143 | Run AI safety/bias/privacy review | Tests hallucinated corrections, dialect/register bias, unsafe content, prompt injection, leakage, subgroup harm, and kill switch. | LNG-142, LNG-111 |
| LNG-144 | Build constrained conversation practice | Original level-aware scenarios, pauses/retries/transcript, bounded rubric, reports, cost budget, and non-AI completion path exist. | LNG-140, LNG-143 |
| LNG-145 | Build open-writing assessment only after calibration | Rubric is visible, human-calibrated, appealable, and formative rather than final grading. | LNG-143, LNG-123 |

## E15 — subscription and enrichment (post-MVP)

| ID | Issue | Done when | Depends on |
| --- | --- | --- | --- |
| LNG-150 | Approve entitlement/pricing matrix | Product/legal sign-off proves core learning, feedback, review, and accommodations remain available free. | LNG-006 |
| LNG-151 | Build honest upgrade experience | Benefit, price, trial, renewal, cancellation, and continue-free are equally clear; never interrupt a mistake. | LNG-150 |
| LNG-152 | Implement billing lifecycle | Purchase/trial/renewal/restore/failure/cancel/refund states are server-validated, idempotent, and supportable. | PAS subscription capability |
| LNG-153 | Add optional enrichment | Offline convenience, enhanced analytics, or advanced practice are supplemental; a free non-AI path reaches each curriculum outcome. | LNG-150, LNG-144 |
| LNG-154 | Define ads policy if ever adopted | No ads during lessons/feedback/review, no behavioural ads for minors, and disclosed frequency/targeting. | LNG-112, LNG-150 |

## Dependency and release path

```text
E00 → E01 → E02 → E03
                   ├→ E04 → E05 → E06 → E07
                   ├→ E08
                   └→ E09 + E10 + E11 + E12

E04–E12 complete → limited learner pilot → public MVP gate
public MVP evidence → E13 / E14 / E15
```

The critical technical sequence is immutable content versions plus scoped action
tests **before** lesson runtime, then deterministic answer evaluation plus golden
corpus **before** adaptive scoring. The critical product sequence is a useful,
accessible course/review loop **before** social competition, subscription
friction, or generative conversation.

## Closed-alpha vertical slice

Before the full A1 course, author and test 5–10 lessons with four exercise
evaluators, rights-cleared audio, feedback/reference cards, checkpoint/resume,
guest-to-account migration, report/rollback, and accessibility evidence. Use this
slice to correct false negatives, content defects, and review friction. Do not
commit to a full authoring workspace, calibrated adaptive placement, downloaded
course packs, social features, commerce, speech, or learner-facing AI until it
has been evaluated with real learners.

## Issue creation order

Create R0 and R1 issues first. Do not bulk-create later-phase issues in a tracker
until the pilot validates the first course and the PAS Lango Learn app/repository has a
settled, owned identifier. Use the IDs above as stable import keys; each row is a
separately estimable issue, with acceptance criteria already in its “Done when”
column.
