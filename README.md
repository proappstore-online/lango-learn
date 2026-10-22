# Lango Learn

Lango Learn is a PAS-hosted language-learning app preparing an original first
course. The current web app is a branded shell; lessons and learner progress
are planned in the [backlog](docs/comprehensive-epics-and-issues.md). The
[architecture decisions](docs/architecture.md) record the client/server
boundary and conventions for the upcoming course and data work.

Run it locally with `pnpm install && pnpm dev`. Use `pnpm typecheck`,
`pnpm test`, and `pnpm build` to check it; the build runs the PAS compliance
check before compiling the web app.

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
- `.github/workflows/` — deploy (R2, keyless OIDC), compliance (MIT + brand + PWA), CI (typecheck); worker step runs only when `worker/package.json` exists.
- `.gitignore` — excludes node_modules, dist, .env files.

## License

MIT.
