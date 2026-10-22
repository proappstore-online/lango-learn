# Lango Learn

Lango Learn is a PAS-hosted language-learning app preparing an original first
course. The current web app is a branded shell; lessons and learner progress
are planned in the [backlog](docs/comprehensive-epics-and-issues.md). The
[architecture decisions](docs/architecture.md) record the client/server
boundary and conventions for the upcoming course and data work.
The [environment/config contract](docs/config-contract.md) defines feature
defaults, media limits, browser support, and the public/private boundary.
The [language capability contract](docs/language-capabilities.md) defines
conservative per-language rules and fixtures for future authored courses.
The [initial D1 data model](docs/data-model.md) describes the additive learning
tables, ownership keys, version relationships, and migration checks.

Run it locally with `pnpm install && pnpm dev`. The pull-request and main-branch
CI runs `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm check:languages`, `pnpm check:migrations`,
`pnpm check:actions`, `pnpm build`, and `pnpm test:e2e`. The build runs the PAS
compliance check before compiling the web app. To run the browser checks locally,
install Chromium once with `pnpm exec playwright install chromium`.
The [accessibility manual-review checklist](docs/accessibility-manual-review.md)
tracks device and screen-reader checks that browser automation cannot complete.

The migration gate validates additive, ordered, idempotent D1 SQL in a fresh
SQLite database. The action gate executes every current `mcp.json` action as
two learners and rejects untested new actions. The browser checks exercise the
signed-out ProShell entry on `/` and `/about`; authenticated lesson flows will
need their own fixtures when they are added.

The app has no worker today. PAS can host one later for schedules, webhooks,
or server routes if those features require it.

## What's in here

- `web/` — Vite + React + TypeScript app, ESM-only, Tailwind 4 via CSS variables.
- `web/src/App.tsx` — Lango Learn shell with `initPro()` + `useAuth()` and app-owned branding.
- `web/src/index.css` — Platform design system (Manrope + Fraunces fonts, full light/dark theme tokens).
- `web/index.html` — App-owned PWA and link-preview meta tags, font preloading, analytics script.
- `web/public/icon-192.png` and `web/public/icon-512.png` — browser and install icons.
- `web/public/og-image.png` — neutral 1200x630 shared-link preview image for `https://lango-learn.proappstore.online`.
- `marketing/` — Astro + Tailwind (pinned) static marketing site for `https://about-lango-learn.proappstore.online`: home, Privacy Policy and Terms & Conditions. Copy, owner, contact and brand colours (mapped into the Tailwind theme) live in `marketing/src/site.ts`. `pnpm build:marketing` writes static HTML to `marketing/dist/`; `pnpm dev:marketing` previews it.
- `package.json` — pnpm workspace, `dev` / `build` / `typecheck` scripts. `prebuild` runs platform compliance check.
- `.github/workflows/` — deploy (R2, keyless OIDC), compliance (MIT + brand + PWA), CI (seven checks); worker step runs only when `worker/package.json` exists.
- `.gitignore` — excludes node_modules, dist, .env files.

## License

MIT.
