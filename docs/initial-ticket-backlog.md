# Lango Learn: initial ticket backlog

Date: 2026-10-20  
Status: draft, ready to import into an issue tracker after PAS is connected.

## Release framing

**MVP outcome:** a learner can choose the initial language pair, receive an
appropriate starting plan, complete an original A1 course, understand feedback,
and return for targeted spaced review.

**MVP scope:** one language pair, A1 only, author-reviewed curriculum, four
exercise types, guest/account progress, placement, course map, review, progress,
notifications, and accessibility basics.

**Explicitly deferred:** social graph, leaderboards, ads, subscriptions, family
plans, punitive attempt systems, rich scenario content, and AI conversation.

## Epic E1 — foundations, identity, and privacy

- [ ] **LINGO-1 — Guest and authenticated learner profiles.** Create a guest
  profile; sign in safely; migrate progress on account creation; persist profile
  and course state across devices.
- [ ] **LINGO-2 — Consent and preference centre.** Capture notification,
  analytics, microphone, and accessibility choices separately; store timezone and
  locale.
- [ ] **LINGO-3 — Learner data controls.** Export and delete account data;
  delete speech recordings/transcripts independently where applicable.
- [ ] **LINGO-4 — Learning event taxonomy.** Define immutable event names and
  payloads for lesson starts, answers, feedback, review, completion, reminders,
  and reports; exclude answer text/voice unless explicitly consented.

## Epic E2 — curriculum platform and editorial quality

- [ ] **LINGO-5 — Curriculum schema.** Model language pair, CEFR band, Can-Do
  outcome, section, unit, lesson, knowledge component, vocabulary item, grammar
  reference, prerequisite, and version.
- [ ] **LINGO-6 — Course progression graph.** Represent units and lesson nodes;
  unlock based on documented prerequisites and preserve learner progress through
  curriculum updates.
- [ ] **LINGO-7 — Authoring workspace.** Create/edit lesson content, media,
  hints, explanations, answer variants, and source metadata without code changes.
- [ ] **LINGO-8 — Publish/version/rollback.** Preview content, publish immutable
  versions, roll back safely, and migrate affected learner state.
- [ ] **LINGO-9 — Editorial QA gate.** Require learning-objective review,
  native-speaker approval, accessibility checks, and automated content validation
  before publication.

## Epic E3 — onboarding and placement

- [ ] **LINGO-10 — Language, level, and goal selection.** Select learning and
  interface languages; choose beginner/placement; set a flexible daily goal.
- [ ] **LINGO-11 — Adaptive diagnostic.** Deliver a compact assessment, produce a
  suggested start with confidence, and permit reassessment/restart.
- [ ] **LINGO-12 — Initial learning plan.** Translate placement and goal into the
  next lesson, review recommendation, and first-week plan.
- [ ] **LINGO-13 — First-session completion.** Finish an original first lesson,
  explain feedback and Review, then request reminders only after value is shown.

## Epic E4 — lesson runtime and evaluation

- [ ] **LINGO-14 — Lesson session orchestration.** Load authored lessons,
  checkpoint progress, resume safely, and emit the event taxonomy.
- [ ] **LINGO-15 — Exercise templates.** Implement original recognition,
  word-construction, typed-recall, and listening exercises with content-defined
  prompts, distractors, hints, and feedback.
- [ ] **LINGO-16 — Audio and accessibility controls.** Support author-supplied
  audio/TTS, replay/slow playback, captions, keyboard use, screen readers,
  reduced motion, and non-audio alternatives.
- [ ] **LINGO-17 — Answer evaluator.** Normalise punctuation/case/diacritics as
  appropriate; apply content-defined accepted variants; return deterministic
  result codes.
- [ ] **LINGO-18 — Learning feedback.** Show correctness, concise explanation,
  targeted hint, retry path, and reference-card link for each exercise.
- [ ] **LINGO-19 — Answer-quality report.** Let learners report an invalid
  rejection or content problem; attach safe context, queue for editorial review,
  and retain the audit outcome.

## Epic E5 — mastery and review

- [ ] **LINGO-20 — Knowledge and exposure ledger.** Record each item/skill
  exposure, response, confidence, and completion without making opaque mastery
  claims.
- [ ] **LINGO-21 — Spaced-retrieval scheduler.** Calculate due review using
  learner history; make the policy versioned and testable.
- [ ] **LINGO-22 — Review hub.** Provide Mistakes, Words, Listening, and
  recommended review as first-class choices, with a transparent “why this” cue.
- [ ] **LINGO-23 — On-demand practice.** Let a learner select a completed unit or
  skill for a focused practice session.
- [ ] **LINGO-24 — Adaptivity guardrails.** Adapt difficulty only within explicit
  content bounds; prevent accidental skipping and allow learner override.
- [ ] **LINGO-25 — Learner progress view.** Surface completed Can-Do outcomes,
  current review load, and meaningful progress without copying another app's
  score system.

## Epic E6 — course experience and milestones

- [ ] **LINGO-26 — Course map.** Show completed, current, review, and upcoming
  units; distinguish progression from optional practice.
- [ ] **LINGO-27 — Unit reference cards.** Surface vocabulary, grammar,
  pronunciation, and examples within the unit and from feedback.
- [ ] **LINGO-28 — Unit checkpoint.** Build a fair, accessible assessment that
  tests the unit Can-Do outcome and routes weak skills to Review.
- [ ] **LINGO-29 — Original proficiency indicator.** Map evidence to Lango Learn's own
  CEFR-referenced capability display; document its limitations.
- [ ] **LINGO-30 — Revisit completed content.** Permit review and replay without
  undoing completion or forcing re-progression.

## Epic E7 — healthy habit loop (MVP-light)

- [ ] **LINGO-31 — Daily-goal and habit calculator.** Compute configurable daily
  activity in the learner timezone; separate it from course proficiency.
- [ ] **LINGO-32 — Original milestones.** Design Lango Learn-specific celebrations and
  rewards with no borrowed names, visuals, sounds, or interaction patterns.
- [ ] **LINGO-33 — Respectful reminders.** Schedule opt-in reminders; support
  quiet hours, easy disable, and smart frequency caps.
- [ ] **LINGO-34 — Grace/return flow.** Offer an optional restorative return after
  missed study, never a destructive loss of earned learning progress.

## Epic E8 — authored rich practice (post-MVP)

- [ ] **LINGO-35 — Dialogue and listening player.** Build authored, original
  multi-turn dialogues with transcript, comprehension checks, and replay.
- [ ] **LINGO-36 — Script and alphabet trainer.** Support writing systems when
  relevant to a course.
- [ ] **LINGO-37 — Accessible timed practice.** Offer an optional, adjustable,
  non-essential speed challenge.
- [ ] **LINGO-38 — Original scenario practice.** Add contextual task-based
  exercises with Lango Learn-created settings and characters.

## Epic E9 — social, only after core validation

- [ ] **LINGO-39 — Privacy-safe connections.** Block/report controls, contact
  discovery consent, private defaults, and age-appropriate handling.
- [ ] **LINGO-40 — Co-operative weekly goal.** Optional partner challenge based on
  meaningful study, not raw grinding.
- [ ] **LINGO-41 — Encouragement feed.** Bounded reactions/milestones with
  moderation and notification controls.
- [ ] **LINGO-42 — Opt-in ranking.** Anti-cheat, moderation, season rules, and
  quality-weighted scoring before any public competition.

## Epic E10 — commerce (post-core)

- [ ] **LINGO-43 — Entitlement layer.** Central entitlement definitions that do
  not alter fundamental course access or review.
- [ ] **LINGO-44 — Dismissible purchase/trial UX.** Clear value, transparent
  pricing, no navigation replacement, and no forced trial.
- [ ] **LINGO-45 — Subscription and shared plans.** Purchase, restore, manage,
  cancel, and optionally invite authorised members.
- [ ] **LINGO-46 — Billing reconciliation.** Verify webhooks, recover purchase
  state, record support evidence, and prevent accidental double entitlement.

## Epic E11 — conversation and speaking (post-core)

- [ ] **LINGO-47 — Speech permission and capture.** Explicit microphone consent,
  recording indicators, diagnostic help, and text alternative.
- [ ] **LINGO-48 — Constrained scenario conversation.** Build opt-in, level-aware
  conversation around Lango Learn-authored scenarios with pause/retry controls.
- [ ] **LINGO-49 — Safe feedback rubric.** Provide constructive, bounded feedback
  and moderation/safety controls; never present uncertain AI output as fact.
- [ ] **LINGO-50 — Conversation retention and cost controls.** Per-session
  consent, transcript deletion/export, rate limits, usage budgets, and fallback.

## Epic E12 — trust, efficacy, and operations

- [ ] **LINGO-51 — Content issue operations.** Triage queues, severity,
  assignment, audit trail, learner resolution, and rollback linkage.
- [ ] **LINGO-52 — Accessibility acceptance suite.** Automated and manual checks
  for captions, screen readers, keyboard navigation, contrast, motion, and audio
  alternatives.
- [ ] **LINGO-53 — Analytics and experimentation controls.** Cohorts, retention,
  lesson drop-off, feature flags, exposure logging, release notes, and rollback.
- [ ] **LINGO-54 — Learning-efficacy evaluation.** Define success measures,
  pre/post assessments, informed consent, curriculum quality sampling, and
  anti-fraud controls.

## Suggested delivery sequence

1. E1, E2, E3, and a vertical slice of E4.
2. Complete E4–E6 and E7 tickets 31/33 for the first learning loop.
3. Validate completion, review uptake, return rate, answer accuracy, and
   accessibility with real learners; fix E2/E4/E5 gaps before expanding scope.
4. Add E8, then decide whether E9, E10, or E11 serves validated learner needs.

## Acceptance gates before public MVP

- Every published item has a Can-Do objective, editor approval, and an
  accessible presentation.
- All answer evaluation supports documented valid variants or has a rapid report
  and remediation path.
- A learner can finish a lesson, understand feedback, locate review, and return
  after a missed day without a punitive dead end.
- No feature blocks normal learning behind payment, social participation, or AI.
- Privacy, deletion, notification, and accessibility controls have been tested.
