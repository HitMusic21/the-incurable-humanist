# Frontend — The Incurable Humanist

React 18 + TypeScript single-page app, built with Vite and styled with Tailwind
CSS. Routing is React Router v6; product analytics is PostHog.

## Running

From this directory (or use the `fe-*` targets in the repo-root `Makefile`):

```bash
npm ci
npm run dev          # vite dev server on :5173
```

In dev the app calls the backend directly at `http://localhost:8000`. Point it
elsewhere with `VITE_API_URL`. Base-URL resolution lives in `src/config/api.ts`.

## Checks

```bash
npm run test         # vitest run
npm run typecheck    # tsc --noEmit
npm run lint         # eslint .
npm run build        # tsc -b, vite build, sitemap generation, prerender
```

Tests are vitest + jsdom + Testing Library, in `src/**/__tests__/`. Run a single
file with `npx vitest run src/components/__tests__/AppSmoke.test.tsx`.

`npm run build` is more than a bundle: after `vite build` it runs
`scripts/generate-sitemap.mjs` and `scripts/prerender.mjs`.

## Layout

```
src/
  main.tsx        entry — router table + PostHogProvider
  shell/App.tsx   layout shell (header/footer, <Outlet/>)
  pages/          Home, About, Archive, EssayDetail, Speak, TopicLanding,
                  Listen, Links, Subscribed, NotFound
    admin/        Login, StoriesIndex, StoryEditor (auth-gated)
  components/     reusable UI (SEO, ConsentBanner, SubscribeCTA, RequireAuth, …)
  lib/            analytics, schema (JSON-LD), utm, adminAuth, date
  config/         api.ts (base URL + endpoint map), site.ts (branding/nav)
  hooks/          useAnalytics, useScrollDepth
  data/           speaking topics
scripts/          sitemap generation + prerender, run during build
```

## Structural rules

Three conventions are load-bearing. Breaking them is a regression, not a
refactor.

1. **Routing is centralized in `src/main.tsx`.** All routes are declared in one
   `createBrowserRouter` table. Don't scatter route definitions into pages.
2. **`/links` sits outside the `<App />` shell.** It's a bio-link landing page
   with no header or footer, deliberately hidden from nav and the sitemap. Keep
   it as a sibling of the shell route, not a child.
3. **Retired routes redirect; they do not 404.** `/newsletter` → `/`,
   `/press` → `/archive`, `/contact` → `/speak`, plus `/essays` → `/archive` and
   `/admin` → `/admin/stories`. These protect inbound link equity and ad landing
   pages — preserve them when reshaping routes.

Two more worth knowing before you touch analytics or `<head>`: `analytics.track()`
is a no-op until consent is granted, and marketing pixels are lazy-loaded only
after consent. `src/components/SEO.tsx` mutates `document.head` directly — there
is no react-helmet. Details in the root CLAUDE.md.

## Deployment

The frontend ships as an **nginx container on Cloud Run**, not a static host.
`Dockerfile` builds the bundle with Node 20, then serves `dist/` from
`nginx:alpine` on port 8080.

`nginx.conf.template` is rendered at container start via `envsubst`, injecting:

- `BACKEND_URL` — where `/api/*` is proxied (the `/api` prefix is stripped before
  it reaches the backend, which is why endpoint strings in `config/api.ts` are
  prefix-free)
- `PORT` — supplied by Cloud Run

Cloud Build handles the image build and deploy; see `cloudbuild.yaml` and
`GCP_DEPLOYMENT.md` at the repo root.

## More

Architecture, analytics/consent invariants, and UI conventions are documented in
the root **[CLAUDE.md](../CLAUDE.md)**. Design system: **`docs/UI_DESIGN_SYSTEM.md`**.
UI fix log: **[CHANGELOG.md](./CHANGELOG.md)**.
