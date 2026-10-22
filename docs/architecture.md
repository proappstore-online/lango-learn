# Lango Learn architecture decisions

Lango Learn is a PAS-hosted language-learning app. Today it serves a React
shell that explains the planned course; it has no published lessons or learner
progress flow. This record distinguishes the checked-in scaffold from decisions
for the course, exercise, and progress work that follows. The
[planning backlog](comprehensive-epics-and-issues.md) sets the delivery order.

## Client and server boundaries

**Decision.** `web/` is a browser-rendered React/Vite/TypeScript app. It owns
navigation, accessible lesson presentation, and local interaction state. It
must not decide authoritative answer correctness, publication state, learner
ownership, or durable progress. The PAS platform owns authentication and
executes registered `mcp.json` actions against the app's D1 database. User
facing data access goes through `app.actions.call(...)`, with authorization
enforced by action metadata and SQL scoping. `migrations.json` is the schema
source applied before action registration and frontend upload. Media that must
remain private belongs in private R2, not the public web bundle.

**Rationale.** A browser can be modified by its user. Server-side checks are
needed for another learner's progress, staff publication, idempotent writes,
and the deterministic exercise evaluator. The deploy order keeps actions from
referencing schema that has not been applied. An optional app worker can host
scheduled jobs, webhooks, or server routes when those workloads arrive; this
repo has no `worker/` directory now, and ordinary D1 actions do not need one.

**Code references.** [`web/src/main.tsx`](../web/src/main.tsx) mounts the SPA;
[`web/src/App.tsx`](../web/src/App.tsx) calls `initPro({ appId: 'lango-learn' })`
and uses `useAuth()` and `ProShell`. [`mcp.json`](../mcp.json) declares the
current server-side action contract. [`migrations.json`](../migrations.json)
declares D1 schema. [The deploy workflow](../.github/workflows/deploy.yml)
applies migrations, registers actions, and uploads the Vite build. The
[PAS action documentation](https://docs.proappstore.online/mcp-app-tools/)
describes the executor and SDK call path.

## UUIDs and identity

**Decision.** D1 entity primary keys use `id TEXT PRIMARY KEY` and contain
UUIDs. For a single-row action, let PAS generate a fresh ID with `:__uuid`.
When an atomic batch needs the same new ID in several statements, generate
one UUID for the request and bind it as a declared parameter; `:__uuid` is
generated separately per occurrence. Treat IDs as opaque strings in the
client. A learner-owned row has an explicit `user_id` and every learner action
scopes reads and writes to the PAS-injected `:__user_id`. Client-provided owner
IDs are never an authorization source.

**Rationale.** Stable text IDs work across course versions and synced
sessions without guessable sequential identifiers. Identity must come from
the authenticated PAS session, not an editable request parameter.

**Code references.** [`migrations.json`](../migrations.json) defines the
scaffold `items.id` as `TEXT PRIMARY KEY` and `items.user_id` as `TEXT`.
[`mcp.json`](../mcp.json) uses `:__uuid` on insert and scopes all three item
actions with `:__user_id`. This is a scaffold example, not a course table.
The [PAS data standard](https://docs.proappstore.online/standard/data/)
specifies text UUID keys and server-derived identity.

## Time and timestamps

**Decision.** Persist timestamps as UTC Unix epoch **milliseconds** in D1
`INTEGER` columns. Every table has `created_at INTEGER NOT NULL`; mutable rows
also get `updated_at INTEGER` when introduced. PAS actions set these values
with `:__now`, including updates. Convert to localized display time only in
the browser. Later daily-goal calculations must use the learner's declared
timezone and handle daylight-saving changes; a UTC timestamp alone does not
define a learner's study day.

**Rationale.** A single numeric representation sorts reliably and avoids
client clock drift. Keeping display timezone separate preserves the source
event time while supporting learners in different regions.

**Code references.** [`migrations.json`](../migrations.json) currently has
`items.created_at INTEGER NOT NULL`, with no `updated_at` yet.
[`mcp.json`](../mcp.json) inserts `:__now`. PAS defines `:__now` as milliseconds
since epoch in its [action documentation](https://docs.proappstore.online/mcp-app-tools/).

## Errors

**Decision.** Use the PAS action response and SDK failure path as the
transport-level error contract. The client must show a distinct error state
for failed data calls and must not turn a failed lesson, vocabulary, or
progress read into an empty result. Distinguish sign-in required (401),
forbidden (403), invalid input (4xx), rate limiting (429), and platform or
network failure (5xx/offline) in user-facing handling. Keep logs free of raw
answers, audio, tokens, and private action parameters. When the deterministic
answer evaluator is built, it will define its own stable educational result
codes separately from transport failures.

**Rationale.** A failed request cannot be mistaken for a learner having no
lessons or progress. PAS already returns structured HTTP failures and the SDK
surfaces action failures; inventing an app-level error envelope now would
claim a contract that the scaffold does not implement.

**Code references.** [`web/src/App.tsx`](../web/src/App.tsx) makes no data calls
yet, so there is no Lango Learn error shape in code. The
[PAS data standard](https://docs.proappstore.online/standard/data/) requires
explicit UI error states and logging for SDK failures. LNG-056 and LNG-060
in the [backlog](comprehensive-epics-and-issues.md) own evaluator result codes
and learning-error taxonomy.

## Pagination

**Decision.** New list actions for lessons, vocabulary, reports, and learner
history use bounded keyset pagination. Declare a capped `limit` plus an
optional cursor over a stable sort key; return enough sort-key data for the
client to request the next page. For rows sorted newest first, use
`created_at DESC, id DESC` and continue with the pair
`(created_at, id) < (:before_created_at, :before_id)`, scoped to the caller
where applicable. A release version must also be part of a course-content
page's query so a page cannot mix revisions. The cursor is an input to a
scoped query, never an authorization credential. Offset pagination is not the
default for changing learner history.

**Rationale.** A deterministic tie-breaker avoids duplicate or skipped rows
when timestamps match. Keyset pagination remains stable as new attempts or
reports arrive. The manifest has no built-in pagination envelope, so each
action must declare its own cursor inputs and result fields.

**Code references.** The scaffold [`list_items` action](../mcp.json) currently
offers only `limit` (default 20, maximum 100), ordered by `created_at DESC`;
it has no cursor or tie-breaker. It is a placeholder, not the convention for
new course actions. PAS supports typed action parameters and keyset queries
through the [manifest contract](https://docs.proappstore.online/mcp-app-tools/).

## Content versions and publication

**Decision.** Published lessons, exercises, vocabulary, answer variants, and
their referenced media belong to an immutable course-version snapshot.
Course-content rows introduced by LNG-020/LNG-030 use a nonnegative integer
`content_version` that increases with each published revision within its
own stable content ID. The active release points to a specific immutable
course version. An in-progress session records the exact course and exercise
version it began with; publishing or rolling back does not rewrite its
history. Content package and evaluator policy versions must remain
reconstructable for attempt review. The client may cache a published snapshot
under its versioned key and refresh when the active release version changes;
drafts and private media are not placed in a public cache.

**Rationale.** Learners need consistent prompts and grading throughout a
session. Editors need safe rollback and an audit trail when a correction
changes accepted answers. Version-keyed caching avoids serving stale content
after publication without treating the browser cache as the release authority.

**Code references.** The current [`migrations.json`](../migrations.json) has
only an `items` table and no `content_version`; this is a decision for later
migrations, not an existing column. LNG-037, LNG-051, and LNG-056 in the
[backlog](comprehensive-epics-and-issues.md) specify immutable releases,
session snapshots, and authoritative evaluation.

## PAS action names

**Decision.** Registered action names use lowercase snake case with a verb
and singular or plural resource, consistently `<verb>_<resource>`: for
example, `list_lessons`, `get_lesson`, `upsert_progress`, and
`search_vocabulary` when those actions are implemented. Names should describe
one operation and remain stable because the SDK and MCP clients call them by
name. Declare typed parameters and `requires_auth` explicitly; learner data
actions scope SQL with `:__user_id`, while staff actions additionally require
the appropriate PAS app role and audited writes. Avoid treating a name as an
authorization boundary.

**Rationale.** The checked-in manifest already uses `list_items`, `get_item`,
and `create_item`. PAS allows only lowercase letters, digits, and underscores
in tool names; dotted names such as `lessons.list` would fail registration.
Verb-first snake case retains the existing style and the platform contract.

**Code references.** [`mcp.json`](../mcp.json) contains the three authenticated,
user-scoped scaffold actions. They remain placeholders until course and
progress actions replace them. The
[PAS manifest specification](https://docs.proappstore.online/mcp-app-tools/)
defines the accepted name characters and role/auth metadata.
