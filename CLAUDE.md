# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**The Incurable Humanist (TIH2)** — a personal publication platform for Denise Rodriguez Dao. Full-stack app with a FastAPI async backend, React + TypeScript frontend, PostgreSQL, and Cloud Run deployment via Cloud Build.

## Common Commands

The `Makefile` at repo root is the canonical entry point for most commands; the raw commands work too.

### Backend (run from repo root)

```bash
source backend/venv/bin/activate                                  # activate venv
make be-install                                                   # pip install -r backend/requirements.txt
make be-run                                                       # uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000
make be-test                                                      # pytest -q (testpaths=backend/tests)
make be-lint                                                      # ruff check backend && flake8 backend
make be-format                                                    # black backend && isort backend

pytest backend/tests/contract/test_auth_api.py -q                 # run a single test file
pytest backend/tests/contract/test_auth_api.py::test_name -q      # run a single test
```

### Frontend (run from repo root)

```bash
make fe-install     # cd frontend && npm ci
make fe-dev         # vite dev server on :5173
make fe-build       # tsc -b && vite build
make fe-test        # vitest run
make fe-lint        # eslint .
make fe-typecheck   # tsc --noEmit

cd frontend && npx vitest run src/components/__tests__/AppSmoke.test.tsx  # single test
```

### Alembic Migrations

Alembic is configured (`backend/alembic.ini`, `backend/alembic/env.py`) with `target_metadata = SQLModel.metadata`. Migrations live in `backend/alembic/versions/` (currently empty — schema is auto-created at app startup via `init_db()`, see architecture notes).

```bash
alembic -c backend/alembic.ini revision --autogenerate -m "message"
alembic -c backend/alembic.ini upgrade head
```

### Docker / Full Stack

```bash
docker compose up --build   # db, backend, frontend (see port note below)
```

`docker-compose.override.yml` (untracked, present locally) remaps host ports to avoid collisions with the native dev servers: **db `5433`, backend `8010`, frontend `5180`**. The container-internal ports (`5432`, `8000`, `8080` — nginx serves the frontend build on `8080`, not `80`) are unchanged. If you point the frontend at the compose backend, use `http://localhost:8010`, not `:8000`.

## Architecture

### Backend layout (`backend/app/`)

```
main.py              # FastAPI entry, lifespan → init_db(), CORS, router mounts
api/                 # HTTP layer — auth.py, newsletter.py, schemas.py (Pydantic)
services/            # business logic — auth.py (register/authenticate/token)
core/                # cross-cutting — database.py, config.py, settings.py, security.py
models/              # SQLModel tables — User, Story, Theme, StoryTheme, Comment,
                     #   Bookmark, ReadingProgress, NewsletterSubscription
```

Routers are mounted with prefixes in `main.py` (`/auth`, `/newsletter`). Additional routers (`stories`, `admin`) are stubbed as TODOs.

### Database lifecycle — important

`app.core.database.init_db()` runs on FastAPI startup and calls `SQLModel.metadata.create_all` inside a retry loop (10 attempts, exponential backoff). Alembic exists but the app currently creates tables imperatively at boot. When adding a new SQLModel, **import it inside `init_db()`** (see the explicit import block in `database.py`) or it won't be registered with `SQLModel.metadata`. Also add it to `app/models/__init__.py` so Alembic autogenerate can see it via `from app.models import *`.

### DATABASE_URL normalization

`app.core.settings.normalize_database_url` runs at import time on the `DATABASE_URL` env var. It:
- Rewrites `postgres://` → `postgresql://`
- Injects the `+asyncpg` driver
- Converts `sslmode=` → `ssl=` (asyncpg uses `ssl`, not `sslmode`)
- Defaults to `ssl=require` unless `DB_SSL=disable` (docker-compose sets this)

Don't hand-craft the URL with `sslmode` or without `+asyncpg` — the normalizer handles it. This exists because Railway Postgres provides URLs in the psycopg format.

### Frontend layout (`frontend/src/`)

```
main.tsx             # entry — createBrowserRouter, PostHogProvider wraps RouterProvider
shell/App.tsx        # layout shell (Outlet), applied to all routes EXCEPT /links
pages/               # route components — Home, About, Archive, Speak, Listen, Links, NotFound
components/          # reusable UI + __tests__/ (vitest + Testing Library)
                     #   incl. SEO, ConsentBanner, SubscribeCTA, PillButton, SocialIconButton
lib/                 # cross-cutting client utilities
  analytics.ts       #   PostHog + GA4 + Meta/TikTok pixels — all consent-gated
  schema.ts          #   JSON-LD @graph builders consumed by <SEO jsonLd={...}/>
  utm.ts             #   UTM param capture/persistence for attribution
config/api.ts        # API base URL resolution (env-aware) + endpoint map + types
config/site.ts       # site-wide branding / nav / social config
```

Routing is centralized in `main.tsx` (React Router v6 data router). Two structural rules:

- **`/links` sits outside `<App />`** — it's a bio-link landing page with no shell chrome and is intentionally hidden from nav + sitemap. Don't add it to the shell's children.
- **Retired routes redirect, they do not 404.** `/newsletter` → `/`, `/press` → `/archive`, `/contact` → `/speak`. Preserve these `<Navigate replace>` entries when reshaping routes — they protect inbound link equity and ad landing pages.

PostHog is initialized once at the provider and uses `VITE_PUBLIC_POSTHOG_KEY` / `VITE_PUBLIC_POSTHOG_HOST`.

### Analytics + consent (frontend)

`src/lib/analytics.ts` is the single entry point for tracking. Two invariants:

1. **`analytics.track()` is a no-op until consent is granted.** Consent state is loaded on boot via `bootConsent()` (called from `main.tsx`) from `localStorage` key `tih_consent_v1` with a 12-month TTL (EU 2026 rule). `ConsentBanner.tsx` is the only UI that flips this.
2. **GA4 / Meta / TikTok pixels are lazy-loaded only after consent** (`loadMarketingTags()`). Do NOT hard-code pixel `<script>` tags in `index.html` — they must remain gated.

When adding a new tracked event, add it to `ANALYTICS_EVENTS` in `lib/analytics.ts` and call `analytics.track(ANALYTICS_EVENTS.YOUR_EVENT, ...)`. Only `newsletter_signup` and `speaker_inquiry` are mirrored to GA4/Meta/TikTok — the rest stay in PostHog. Extend `mirrorConversionEvent` if you add another conversion.

### SEO component

`src/components/SEO.tsx` mutates `document.head` imperatively in a `useEffect` (title, description, canonical, OG, Twitter, robots, and a single JSON-LD `<script id="tih-jsonld-page">`). Every page component should render `<SEO ... />` once. Build the `jsonLd` array with helpers from `src/lib/schema.ts` — the component wraps them in a `@graph`. There is no `react-helmet`; don't introduce one.

### API base URL resolution (frontend)

`src/config/api.ts` picks the base URL in this order:
1. `VITE_API_URL` env var if set
2. `/api` in production (same-origin — nginx proxies `/api/*` → backend, stripping the prefix — see `frontend/nginx.conf.template`)
3. `http://localhost:8000` in dev (Vite dev server hits the backend directly, no proxy)

Endpoint strings in `API_CONFIG.endpoints` are prefix-free (`/leads/subscribe`, `/auth/login`, etc.). The prod `/api` prefix is added by the base URL. Nginx strips it via `rewrite ^/api/(.*)$ /$1 break;` before proxying.

The frontend container reads `BACKEND_URL` at boot (envsubst renders `nginx.conf.template`). In Cloud Run: `--set-env-vars BACKEND_URL=https://tih-backend-xyz.a.run.app`. In docker-compose: pinned to `http://backend:8000` in `frontend/Dockerfile` default.

New API calls should route through `API_CONFIG.endpoints` rather than hard-coding paths.

### Deployment

`cloudbuild.yaml` builds both images from the repo-root context (`-f backend/Dockerfile .` and `-f frontend/Dockerfile .`) and deploys to Cloud Run services `tih-backend` / `tih-frontend`. The Dockerfiles expect the repo root as build context. Legacy Railway support is why the DB normalizer reads `RAILWAY_PUBLIC_DOMAIN` for CORS in `main.py`.

## UI conventions (frontend)

Design system reference: **`docs/UI_DESIGN_SYSTEM.md`**. Keep it in sync when the site's visual language changes. Chronological UI-fix log: **`frontend/CHANGELOG.md`**.

Product/brand docs live in **`docs/`** (checked in). `.claude/docs/` contains the same brand/PRD files and predates the visible copy — treat `docs/` as canonical and update `.claude/docs/` only if a doc is genuinely Claude-only.

The site's visual identity is a **prospectus / literary journal** treatment. Two conventions are load-bearing and should not be regressed:

### 1. Long-form prose measure + justification

Any prose block that reads like body copy (About page bio blocks, essays, etc.) MUST use:
- `max-w-[62ch]` — comfortable serif reading measure (~65-75 chars per line)
- `mx-auto` — centered in its parent card
- `text-justify` — symmetric left/right edges (matches the landing-page prospectus treatment)
- `hyphens-auto` — smooth line-break rhythm
- `leading-[1.75]` — long-form density
- `[text-wrap:pretty]` — avoids widows/orphans on Safari + modern Chrome

Canonical example: `frontend/src/pages/About.tsx` (both prose blocks). Copy that class list rather than inventing a new one.

**Do NOT** use `max-w-3xl` + `leading-relaxed` + default `text-align: left` for prose — that produces the ragged, edge-to-edge line-lengths the 2026-07-19 fix removed.

### 2. Pill CTAs with long labels

Any pill-shaped CTA (`rounded-pill` + `h-12`) that might carry a long label (email address, URL, long phrase) MUST:
- Use `whitespace-nowrap` — pills structurally can't wrap mid-text
- Live in a `flex-wrap` container — buttons drop to a new row on narrow viewports rather than crush each other
- Have a short human-facing label ("Email Denise") + a full descriptive `aria-label` (`aria-label="Email booking@..."`) — screen readers get the full context, visual users get a clean pill
- Include a `focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2` ring — CRITICAL a11y rule
- Include `cursor-pointer`
- Use SVG icons (Heroicons / Lucide style), NEVER emoji icons

Canonical example: `frontend/src/pages/Speak.tsx` (the Email + Press kit pair). If the full email/URL needs to be visible, put it in the trust line below the buttons as an inline underlined `<a>` — never inside the pill.

**Do NOT** put a 32-character email inside a fixed-height pill without `whitespace-nowrap` — that's the exact bug the 2026-07-19 fix removed.

### Docker dev loop

Frontend container serves a **pre-built bundle** (nginx). Edits to `.tsx` files are NOT hot-reloaded — you must rebuild:

```bash
docker compose up -d --build frontend           # normal rebuild
docker compose build --no-cache frontend        # force full rebuild (use when browser shows stale content)
```

For iterative UI work, prefer `make fe-dev` (Vite HMR on `:5173`) and only rebuild the container for final verification.

Browser cache: after a rebuild, hard-reload the browser (Cmd+Shift+R) or DevTools → Network → "Disable cache" is checked. The Docker frontend serves nginx-cached assets that Chrome respects aggressively.

## Code Style

**Python** (`pyproject.toml`, `.flake8`): line length 100, black + isort (profile=black), ruff rules `E,F,I,UP,B,SIM,C4`, ignores `E203,W503`. Pre-commit runs black, ruff (`--fix`), ruff-format, and prettier.

**TypeScript**: strict mode, path alias `@/*` → `src/*` (see `vite.config.ts` + `tsconfig`).

## Testing

- **Backend**: `pytest` with `pytest-asyncio`. Testpaths pinned to `backend/tests` in `pyproject.toml`. Structure: `tests/contract/` (API contract tests), `tests/integration/`, `tests/unit/`. `conftest.py` intentionally does nothing — tables are created by the app's lifespan when it starts. Contract tests currently expect a running app / DB; CI runs `pytest -q || true` so failures don't block.
- **Frontend**: `vitest` with jsdom + Testing Library (`vitest.config.ts`, `vitest.setup.ts`). Tests live in `src/**/__tests__/`.

## CI (`.github/workflows/ci.yml`)

Two jobs on push to `main` and PRs:
- **backend**: Python 3.13, installs requirements + ruff/flake8, lints, runs pytest (non-blocking).
- **frontend**: Node 20, `npm ci`, typecheck, lint (non-blocking), test, build.

Typecheck and tests are the strict gates on the frontend; lint failures are tolerated. Keep that in mind before assuming a green CI means lint-clean.
