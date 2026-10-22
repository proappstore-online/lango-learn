# Authorization and migration contract gate (LNG-025)

`pnpm check:actions` runs all 29 registered action definitions as SQL against
temporary, file-backed SQLite databases with foreign keys enabled. One starts
empty; the other starts with the legacy `0001_init` schema and an existing
item before receiving the later migrations. The gate reapplies the migration
manifest, checks foreign keys, runs the learner, guest import, and staff
journeys, then reopens each database to verify durable audit and import rows.
All fixture users, courses, reports, and guest IDs are synthetic. No course
content or media is shipped as part of the fixture.

The learner journey checks owner-scoped reads and writes, cross-user denial,
progression on a pinned course snapshot, replayed request IDs, stale and
same-millisecond checkpoints, invalid UUIDs, and report and review ownership.
The guest journey checks no pre-auth write, first import, scoped receipts,
cross-account denial, replay, conflicting checkpoints, invalid input, and
rollback and retry after an interrupted batch. The staff journey exercises
author, review, publish, retire, and report triage with each required PAS app
role. It checks all denied cross-role paths, mixed grants, forged request
claims, publication immutability, transition and audit history, stale and
replayed requests, and interrupted batch rollback. A separate file-backed app
database verifies that foreign report and release IDs cannot resolve locally.

The local executor models the PAS server gate from `mcp.json` metadata and
supplies `:__user_id`, `:__uuid`, and `:__now` from its synthetic session. It
rejects request attempts to override those bindings. These tests exercise
the manifest and SQLite constraints. They do not execute against a live PAS
role projection; platform registration and compliance gates check that layer.
