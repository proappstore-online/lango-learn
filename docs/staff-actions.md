# Staff roles and action contract (LNG-022, LNG-024)

PAS app roles are the authority for staff actions. They are checked by the
platform action executor before SQL runs; no request parameter supplies or
overrides a role. The app uses its own D1 database, so a course or report ID
from another app cannot resolve here. These actions intentionally operate on
shared app content or the staff report queue. Each declares a
`caller_unscoped` reason and still records the session's `:__user_id` as the
audit actor. They never return answer text, audio, or private learner progress.

| PAS app role | Actions | Boundary |
| --- | --- | --- |
| `curriculum_editor` | `create_course`, `create_course_version`, `create_lesson`, `create_exercise`, `submit_version_for_review`, `create_course_locale`, `create_course_map`, `create_course_unit`, `place_lesson_in_unit`, `add_lesson_prerequisite` | Author a draft snapshot. |
| `content_reviewer` | `return_version_to_draft`, `approve_course_version` | Review a submitted snapshot. |
| `moderator` | `publish_course_version`, `retire_course_release` | Control the active release. |
| `support` | `list_staff_reports`, `update_report_status` | Read and triage reports across learners. |

The [role contract](../contracts/staff-roles.json) is the complete action
allowlist. Each action in `mcp.json` requires exactly one of these PAS **app**
roles. Grants are independent and additive: a person with two grants gets the
union of those actions; a `curriculum_editor` cannot approve a version and a
`content_reviewer` cannot author one. `support` does not gain publication
control, and `moderator` does not gain the learner report queue. Ordinary
signed-in members have none of these permissions.

Assign or revoke each grant for a known PAS user in the app's Settings → Access
screen (or the equivalent owner-controlled `app.roles.assign` /
`app.roles.revoke` operation). Do not seed staff grants in D1 migrations or
derive them from a platform `creator`/`admin` role, app-team membership, email,
or a browser claim. The assigning operator verifies the person's identity and
grants only the job-specific role; mixed duties require separate grants.
Revocation takes effect at the next server action authorization check. The
`mcp.json` `auth.app_roles` declaration is the executable role configuration;
the platform checks its live app-role assignment before SQL. The action has no
role parameter. `:__user_id` comes from that same authenticated session and
is recorded as the audit actor. The local test executor supplies synthetic
session grants to model the PAS gate and never accepts request data as grants.

This app currently has one app-isolated D1 database, so all staff course and
report actions operate within that app. There is no cross-app ID lookup or
client-selected tenant. If a future change introduces organisations or
workspaces within this app, every staff action must also check that tenant's
membership in SQL; an app role by itself would not grant access to every
tenant. The synthetic matrix checks that foreign IDs and unrelated roles do
not modify local rows.

The lifecycle is `draft → review → approved → published → retired`; a reviewer
may return `review → draft`. Authoring SQL requires a draft version and an
exact `updated_at` checkpoint. Submission requires at least one exercise.
Published lesson and exercise rows have no update action; publishing seals
their course version. An active release is superseded atomically when a newer
approved snapshot is published. Retirement changes release and version status
without deleting content, sessions, attempts, or the historical release row.
An in-progress learner session remains pinned to its original version.

Every write is an atomic PAS `batch`. The first statement inserts an audit row
only when the resource, expected state, version, and request UUID are valid.
Later statements require that exact audit row, actor, resource, action, and
server timestamp. A failed or stale guard writes neither the resource nor an
audit row. A retry uses the same `request_id` UUID; it cannot create a second
audit row or repeat a transition. The action returns per-statement write counts;
zero counts mean the caller should refresh state before making a new request.
Timestamps are server-provided UTC epoch milliseconds and mutable writes
require `:__now > :expected_updated_at` so optimistic concurrency can advance
even under fast retries.
Audit `detail_json` records version and transition context without raw answers
or report text, so later status changes do not erase the event history.

Report triage follows `open → reviewing → resolved|dismissed`. Each audit row
stores the learner's ID as `subject_user_id`, while the report itself retains
its original owner. The support queue is bounded and uses a timestamp/ID
keyset cursor. SQL validates the report's course to prevent a mismatched ID
from mutating another course's report. No learner ownership is inferred from
a client-supplied ID.

`pnpm check:actions` executes the manifest against the committed migrations
with foreign keys enabled. Its synthetic fixtures test each role, every denied
cross-role path, mixed grants, forged client claims, signed-out callers, stale
and replayed requests, duplicate authoring, course mismatch, published
immutability, report ownership, audit rows, failed-batch rollback, and
retirement. There is no original course content or media in this change.

The course-map authoring contract and locale normalization rules are in [course-map.md](course-map.md).
