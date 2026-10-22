# Scoped learner actions (LNG-021)

All learner actions in `mcp.json` require a PAS session and use its injected
`:__user_id` for every statement. IDs supplied by a caller identify a resource
or an idempotency request; they never establish ownership. D1 foreign keys and
the partial unique index on active `(user_id, lesson_id)` sessions back the SQL
guards. Timestamps are server supplied UTC epoch milliseconds (`:__now`), and
single-row generated IDs use `:__uuid`. Multi-statement bootstrap uses a fresh
ID in each insert. The checked-in action fixture exercises the manifest SQL
against the real migrations with foreign keys enabled.

| Flow | Actions | Contract |
| --- | --- | --- |
| Bootstrap | `bootstrap_learner`, `get_learner_bootstrap` | Creates a profile and default preferences once, then reads only the caller's rows and active session. |
| Next/resume | `get_next_lesson`, `start_lesson`, `resume_lesson` | Selects from active published releases, requires earlier lessons in the same snapshot to be complete, and pins a session to its course version and lesson. An already active or completed lesson cannot be started again. |
| Submit/complete | `submit_exercise`, `complete_lesson` | Submission requires the owned active session, the exact next exercise in its pinned lesson, and the last checkpoint timestamp. An atomic batch records an attempt and moves the checkpoint. Completion requires an attempt for every exercise and a matching checkpoint. |
| Review | `list_due_reviews`, `record_review` | Lists only due review rows for the caller. Recording a review requires an owned session and an attempt on that review's source exercise. It records an exposure; scheduling and mastery calculation belong to LNG-071/072. |
| Preferences | `update_preferences` | Replaces declared preference values only when the caller's current `updated_at` matches. |
| Reports | `create_content_report`, `list_content_reports` | A report must refer to an exercise in the caller's session and have a listed category. It intentionally has no answer-text or audio parameter. |

`attempt_id`, `exposure_id`, and `report_id` are client-generated UUID request
IDs. A retry must reuse the same ID; a second insert is ignored. The caller
must read the owned row to distinguish a successful previous call from a
rejected request. `expected_updated_at` implements optimistic concurrency; a
zero-row write means stale input, replay, invalid state, or unavailable data.
The client should refresh the scoped read before retrying. List cursors use
ordered timestamp/ID pairs and bounded limits.

The current schema has no authored answer variants or evaluator. Consequently
`submit_exercise` records the server-owned evaluator policy version and the
fixed result code `pending_evaluation`; it accepts no claimed correctness or
raw answer. `complete_lesson` means that each exercise was attempted, not that
answers were scored or a learning objective was mastered. LNG-056 supplies the
server evaluator before a graded learning flow is released. The action surface
ships without enabling lessons or adding content/assets.
