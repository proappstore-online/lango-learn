# PAS provisioning status

Date checked: 2026-10-20

## Original identifier checks

The official PAS MCP connection was authorised successfully. `whoami` confirmed
the intended account, and the live tool schema and approved-template catalogue
were inspected.

PAS has an existing `lingo` app record:

- Live URL: `https://lingo.proappstore.online` (currently returns 404 / down)
- Repository: `https://github.com/proappstore-online/lingo`
- Data worker: `https://data-lingo.proappstore.online`
- Store listing: `https://proappstore.online/apps/lingo/`

The connected account **does not own** `lingo`; PAS refused owner-scoped project
tools for it. Therefore it must not be reused, repurposed, or provisioned over.
The `list_apps` tool itself currently returns `401 missing bearer token` despite
the authenticated MCP session, so this per-app lookup is the available evidence.

PAS also has an existing `lango` app record at
`https://github.com/proappstore-online/lango`, with a data worker and store
listing; its route is currently down. The same connected account does not own it,
so it also cannot be reused or provisioned over.

## Completed no-change previews

`provision_pas_app` ran with `dry_run: true` for `lingo`, display name `Lingo`,
private repository, approved `template-app`, and verification enabled. It showed
that a live execution would create/reuse the GitHub repository, replace template
placeholders, provision the R2 route, D1 database, data worker, and app record,
then verify repo/deploy/host state. It made no changes.

## Local repository

This local Git repository was created at:

`/Users/serge/dev/stores/pas/apps/lingo`

It contains the research and initial backlog only. It has not been linked to PAS.

## Historical decision

The original proposed next step was a new identifier such as `lingo-learn` or
`learn-lingo`. The creator selected `lango-learn`; the resulting completed
provisioning and its remaining platform deployment blocker are recorded below.

## Provisioned replacement: Lango Learn

After the creator explicitly selected a new name, the official PAS provisioning
workflow created a new private app, **Lango Learn**, with app ID
`lango-learn` (receipt `d9f1414c-7efc-4cce-85fd-156636f044cb`). It is distinct
from both pre-existing `lingo` and `lango` records.

- Repository: https://github.com/proappstore-online/lango-learn
- Intended app URL: https://lango-learn.proappstore.online
- Data worker: https://data-lango-learn.proappstore.online
- D1 database: `pas-data-lango-learn`
- Provisioning: completed (route, D1 database, data worker, app record, and
  private template repository all succeeded)

The initial repository commit is `c6c9901`. The template's CI, compliance, and
deploy workflows are currently cancelled before their first step, so the app URL
returns 404. This is not an application-code failure: GitHub annotated each
check with: “The job was not started because recent account payments have
failed or your spending limit needs to be increased.” The `ubuntu-latest`
migration notice is informational only.

The organisation-wide blocker was already tracked at
[#2 in gcp-spending](https://github.com/proappstore-online/gcp-spending/issues/2).
The Lango Learn evidence and exact failed workflow URLs were added in
[a comment](https://github.com/proappstore-online/gcp-spending/issues/2#issuecomment-6278097716).
The required platform-owner action is GitHub organisation **Settings → Billing
& plans**: resolve the failed payment or raise the GitHub Actions spending
limit, then rerun the latest **Deploy to R2** workflow. No repository code
change can bypass that organisation-level restriction.

## Team capability: verified platform behaviour

PAS supports **app-level** collaboration through its built-in roles:
`owner`, `member`, `moderator`, `editor`, and `viewer`. An app owner can assign
roles and create join-code/link/QR invites for team members. That is a useful
capability for Lango Learn's future internal-content or moderation team.

It does **not** solve this ownership mismatch:

- `owner` is automatically assigned to the app creator.
- PAS invites cannot grant the `owner` role.
- The authenticated PAS MCP tool catalogue exposes no ownership-transfer,
  organisation-membership, repository-collaborator, or platform-admin action.

Therefore an existing app must be accessed by authenticating as its actual owner
or handled by PAS platform support. It cannot be claimed by adding the current
account to an in-app team.

## Platform issues filed

The following upstream PAS platform issues were filed on 2026-10-20:

- [#423 — Add a safe PAS app ownership-transfer workflow](https://github.com/proappstore-online/platform/issues/423)
- [#424 — Make PAS apps easy to find and filter in the creator console](https://github.com/proappstore-online/platform/issues/424)

They request an audited recovery/transfer path for legitimate creators and a
clear app search/filter experience that distinguishes owned, accessible, and
existing-but-inaccessible apps before any provision action is attempted.
