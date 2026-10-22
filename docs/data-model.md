# Initial D1 learning model

`migrations.json` is the deploy source of truth. `0002_learning_model` adds the
tables below without changing the existing `items` scaffold or its actions.
The app's D1 database is app isolated; it has no workspace tenant column.
Within it, learner ownership is the PAS authenticated `user_id`, never a
client selected owner. New learner actions must still require authentication
and scope every read and write by `:__user_id`; a foreign key alone does not
authorize a query. Staff actions require PAS roles and audited writes.

| Area | Tables | Key relationships |
| --- | --- | --- |
| Learner | `learner_profiles`, `learner_preferences` | One profile and preference row per PAS user. Preferences default reminders off. |
| Course snapshot | `courses`, `course_versions`, `lessons`, `exercises` | A version belongs to one course; a lesson belongs to one version; an exercise belongs to one lesson. |
| Activity | `learning_sessions`, `exercise_attempts`, `learning_exposures`, `review_states` | Session owner and exact lesson snapshot are retained. Attempts and exposures must match that owner and lesson. Review state is unique per user, course, and stable content ID. |
| Quality and publication | `content_reports`, `course_releases`, `audit_rows` | Reports retain their learner owner. Releases point to a version of the same course; only one release per course can be active. Audit rows name the actor and affected resource. |

All entity IDs are opaque UUID text in production. New single-row PAS actions
use `:__uuid`; multi-row actions bind one request-generated UUID when the same
ID is reused. All timestamps are UTC epoch milliseconds in `INTEGER` columns,
set by server time (`:__now`), including `created_at` and mutable `updated_at`.
The migration does not seed learners or course content.

`course_versions.content_version` is a nonnegative, course-local integer. Each
version row identifies a course snapshot. Lessons and exercises also retain
their stable content ID and nonnegative content version; their UUIDs identify
the particular snapshot row. The active release points at one course version.
Sessions retain their exact course version and lesson; attempts retain the
exercise row and evaluator policy version. Publishing or rolling back must
create/repoint releases without rewriting those history rows. Future content
actions must prevent edits to published snapshots and enforce review and
publication state; schema relationships alone cannot enforce that workflow.

The indexes cover version lookup, ordered lessons/exercises, scoped resume and
history pages, due review, report queues, active release uniqueness, and audit
lookups. `pnpm check:migrations` applies both migrations twice on SQLite with
foreign keys enabled, checks their additive shape, inserts representative
data, rejects owner and snapshot mismatches, and confirms legacy rows survive
a rerun. `pnpm check:actions` continues to exercise the existing scaffold
actions; LNG-021/022 will add fixtures for new action SQL.


The additive course-map extension is documented in [course-map.md](course-map.md).
The version-scoped objective graph extension is documented in [objective-graph.md](objective-graph.md).
