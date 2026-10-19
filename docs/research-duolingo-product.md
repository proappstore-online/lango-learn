# Research: language-learning product mechanics

Date: 2026-10-20  
Purpose: retain product research so Lango Learn does not need to repeat this discovery.

This document records **product patterns**, not an implementation or design
template. Lango Learn must develop its own name, visual identity, curriculum, copy,
content, interactions, characters, audio, and technical implementation. Do not
copy protected Duolingo material or imply an affiliation.

## What the current product demonstrates

### Entry, onboarding, and course position

- A learner selects a language, chooses a daily goal and may allow reminders.
- Beginners can begin at the start; learners with prior knowledge can take an
  adaptive placement assessment. Placement changes the initial location, while
  prior material remains available to revisit.
- An account/profile persists progress across devices.

Lango Learn implication: onboarding needs a transparent diagnostic, stated confidence,
an easy restart/reassessment path, explicit reminder permission, and a first
session that proves the learning loop quickly.

Official sources:

- [How to use Duolingo for language learning](https://blog.duolingo.com/duolingo-101-how-to-learn-a-language-on-duolingo/)
- [Placement-test partial-credit improvements](https://blog.duolingo.com/partial-credit-improvements-to-duolingos-placement-test/)

### Curriculum and lesson structure

- Course content is organised from sections to units to lesson/path nodes.
- Units communicate a practical goal and focus a limited set of vocabulary and
  grammar; course sections map to CEFR-style proficiency targets.
- Reference material supplies vocabulary, grammar, and pronunciation support.
- Exercises span reading, writing, listening, and speaking. Difficulty can move
  from recognition toward recall and production.

Lango Learn implication: author around explicit Can-Do outcomes and an open curriculum
schema, not a screen-by-screen course. Provide source-language explanations and
unit references at the point of need; do not force a learner to hunt for them.

Official sources:

- [How to use Duolingo for language learning](https://blog.duolingo.com/duolingo-101-how-to-learn-a-language-on-duolingo/)
- [How to review lessons](https://blog.duolingo.com/how-to-review-lessons-on-duolingo/)
- [How courses are evolving](https://blog.duolingo.com/how-are-duolingo-courses-evolving/)
- [Spanish-course learning tips](https://blog.duolingo.com/tips-for-learning-spanish-on-duolingo/)

### Review and adaptivity

- Review is both embedded in the main progression and available on demand.
- Current practice choices include prior mistakes, recommended words, speaking,
  listening, and—where available—longer experiences such as stories or radio.
- Published research describes choosing review based on exposure and recall
  history; product materials describe changing later lesson difficulty based on
  performance.

Lango Learn implication: review must be primary navigation, not a hidden premium
feature. Build a per-item/per-skill mastery model and spaced-retrieval scheduler,
but expose why a recommendation appears and always let the learner choose a
practice mode.

Official sources:

- [Guide to the free Practice tab](https://blog.duolingo.com/guide-to-duolingo-practice-hub/)
- [Adaptive lessons](https://blog.duolingo.com/keeping-you-at-the-frontier-of-learning-with-adaptive-lessons/)
- [How Duolingo learns how learners learn](https://blog.duolingo.com/how-we-learn-how-you-learn/)

### Learning experiences beyond short exercises

- Interactive dialogues/stories and listening experiences add discourse-level
  practice beyond isolated sentences.
- Some courses include alphabet/character instruction.
- Scenario practice, timed challenges, and higher-difficulty completion
  challenges offer alternate ways to practise already introduced skills.
- Intermediate mini-units can introduce a small amount of language then use it
  promptly in dialogue, listening, or conversation.

Lango Learn implication: begin with reliable core exercises, then add authored dialogue
and scenario practice. Any timed mode must be optional and accessible; fluency
practice cannot be reduced to speed alone.

Official sources:

- [Adventures](https://blog.duolingo.com/adventures/)
- [Ways to practise](https://blog.duolingo.com/ways-to-practice-in-duolingo/)
- [Intermediate mini-units](https://blog.duolingo.com/intermediate-mini-units/)

### Progress, habits, and motivation

- Completing lessons/practice earns XP and supports weekly ranking systems.
- A daily streak tracks consecutive days with a completed lesson. Currency and
  missed-day protection support the habit loop.
- Learners can configure goals and reminders; leaderboards can be opted out of.
- Friends can share progress, co-operate on weekly tasks, maintain shared habits,
  and encourage each other.

Lango Learn implication: lead with proficiency and learning consistency, not raw volume.
Use an original, low-pressure habit model: flexible goals, grace days or pauses,
timezone correctness, and opt-in competition/co-operation. Never make learners
feel that a broken streak erases real progress.

Official sources:

- [Duolingo 101: gamification, social features and plans](https://blog.duolingo.com/duolingo-101-how-to-learn-a-language-on-duolingo/)
- [Habit formation and language learning](https://blog.duolingo.com/putting-in-work-the-habit-of-language-learning/)
- [Friends Quests](https://blog.duolingo.com/friends-quests/)
- [Social features](https://blog.duolingo.com/friends-social-features/)

### Monetisation and friction patterns

- The free model has used ads and limited mistake allowances; subscribers receive
  benefits such as no ads and unlimited attempts. Current official materials say
  the Practice tab is free, so it must not be treated as a paywall requirement.
- Higher subscriptions add AI roleplay, video conversation, and explanations.
- Family plans and entitlement differences exist.

Lango Learn implication: core curriculum and review must remain usable without an
upsell. If subscriptions are added, define entitlement rules centrally, make all
marketing dismissible, and never block the normal course path behind an AI or
premium activity.

Official sources:

- [How to use Duolingo for language learning](https://blog.duolingo.com/duolingo-101-how-to-learn-a-language-on-duolingo/)
- [Guide to the free Practice tab](https://blog.duolingo.com/guide-to-duolingo-practice-hub/)
- [Duolingo Max](https://blog.duolingo.com/duolingo-max/)

### AI conversation

- Current conversational features use guided roleplay and real-time audio calls;
  related materials mention transcripts, level/topic awareness, post-call
  feedback, captions, translations, and push-to-talk in some experiences.

Lango Learn implication: this is a post-core feature. It must be opt-in, support quiet
thinking time and text alternatives, record only with clear consent, offer
transcript/recording deletion, enforce cost limits, and supply a non-AI practice
path.

Official sources:

- [Duolingo Max](https://blog.duolingo.com/duolingo-max/)
- [Beginner video call](https://blog.duolingo.com/beginner-video-call-with-falstaff/)
- [2025 product highlights](https://blog.duolingo.com/product-highlights/)

### Progress signals

- A public, per-course score maps progress to CEFR capability descriptions and
  supports comparison across courses.

Lango Learn implication: use an independently designed proficiency signal grounded in
our own Can-Do completion and assessments. Do not reuse another product's score
name or presentation.

Official source: [Duolingo Score](https://blog.duolingo.com/duolingo-score/)

## Community feedback: recurring risks to address

Forum observations are anecdotal rather than product requirements, but repeated
themes are useful design risks to validate with Lango Learn learners.

| Observation | Lango Learn response |
| --- | --- |
| Learners want targeted review for mistakes, vocab, listening, and speaking to be easy to find. | Put Review in primary navigation; offer recommendations and explicit modes. |
| Raw XP competitions can reward repetitive, shallow activity. | Make competition optional; rank quality signals or course milestones rather than repetition alone. |
| Streak loss can create anxiety and abandonment. | Separate learning progress from habit count; offer pauses/grace days and flexible daily goals. |
| Valid answer variants are sometimes rejected. | Normalise language-aware input, support variants, provide an “answer should be accepted” report, audit decisions, and restore attempts when we are wrong. |
| AI-generated material can be unnatural or wrong. | Require editor/native-speaker approval, objective metadata, test coverage, staged release, versioning, and rollback. |
| Conversation is valuable to some and disruptive or inaccessible to others. | Make it optional; support pause/think time, push-to-talk choices, retries, transcripts, and a non-AI alternative. |
| Forced trials or premium interruptions damage trust. | Do not substitute core navigation with promotion or make paid work mandatory for path progress. |
| A correct/incorrect verdict alone is not enough. | Return a concise explanation, relevant hint, and link to the underlying reference. |

Community sources:

- [Practice/navigation feedback](https://www.reddit.com/r/duolingo/comments/1jehwi0/) and [related navigation feedback](https://www.reddit.com/r/duolingo/comments/1jq7fcf/)
- [Competition motivation discussion](https://www.reddit.com/r/duolingo/comments/1pdtqfq/) and [league-pressure feedback](https://www.reddit.com/r/duolingo/comments/1k4yxsp/)
- [Streak-anxiety discussion](https://www.reddit.com/r/duolingo/comments/1i156w5/) and [long-term learner churn](https://www.reddit.com/r/duolingo/comments/1mj4n62/)
- [Answer-variant feedback](https://www.reddit.com/r/duolingo/comments/1rpr7tw/) and [correction-flow request](https://www.reddit.com/r/duolingo/comments/1w57pyp/)
- [AI-course quality feedback](https://www.reddit.com/r/duolingo/comments/1s764x9/)
- [Positive AI-conversation feedback](https://www.reddit.com/r/duolingo/comments/1iki0i6/), [interruption/accessibility feedback](https://www.reddit.com/r/duolingo/comments/1mi7lfe), and [push-to-talk feedback](https://www.reddit.com/r/duolingo/comments/1npkfa3/)
- [Premium-clutter feedback](https://www.reddit.com/r/duolingo/comments/1jvbs17/) and [forced-feature feedback](https://www.reddit.com/r/duolingo/comments/1jukvxa/)

## Research decisions

1. Build the learning loop and curriculum quality before social, monetisation, or
   generative conversation.
2. Start with one language pair, one CEFR band, and four robust exercise types.
3. Make review learner-controlled as well as adaptive.
4. Treat content quality, answer evaluation, accessibility, and learner trust as
   launch criteria—not follow-up polish.
