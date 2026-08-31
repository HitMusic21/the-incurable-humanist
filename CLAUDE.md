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
make tick                                                         # fire the welcome-sequence scheduler locally
                                                                  #   POST $BACKEND_URL/leads/sequence/tick
                                                                  #   defaults: BACKEND_URL=:8010, SCHEDULER_TOKEN=dev-tick-token

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

### Aggregate gates (run before committing)

```bash
make lint    # be-lint + fe-lint
make test    # be-test + fe-test
```

### Alembic Migrations

Alembic is configured (`backend/alembic.ini`, `backend/alembic/env.py`) with `target_metadata = SQLModel.metadata`. `backend/alembic/versions/` holds a linear chain — head is **`0005_story_sync_fields`**. Note `0001_baseline` is an intentional no-op: the chain assumes tables already exist from `init_db()`'s `create_all`, so every migration is written inspect-first and no-ops when a column or index is already there.

**On a brand-new database**, run the app once (or `init_db()`) to create the tables, then `alembic stamp head`. Running `alembic upgrade head` against a truly empty DB fails with `NoSuchTableError` — the migrations alter tables, they don't create them.

Alembic needs the **async** URL. A `postgresql://` URL fails with *"The asyncio extension requires an async driver"*:

```bash
DATABASE_URL='postgresql+asyncpg://postgres:postgres@localhost:5433/tih_dev' \
  alembic -c backend/alembic.ini upgrade head
```

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
api/                 # HTTP layer — auth.py, newsletter.py, leads.py, stories.py,
                     #   schemas.py (Pydantic)
services/            # business logic — auth.py, email.py, substack_sync.py,
                     #   html_sanitize.py, sendgrid_webhook.py, posthog_server.py, slugify.py
core/                # cross-cutting — database.py, config.py, db_url.py, security.py
models/              # SQLModel tables — User, Story, Theme, StoryTheme, Comment,
                     #   Bookmark, ReadingProgress, NewsletterSubscription,
                     #   LeadCapture, LeadEvent
```

Routers are mounted with prefixes in `main.py` (`/auth`, `/newsletter`, `/leads`, `/stories`). There is **no separate `admin` router** — the admin surface lives on the `stories` router and is distinguished by method, not prefix:

| Public | Admin (bearer token) |
|---|---|
| `GET /stories`, `GET /stories/{slug}` | `GET /stories/id/{id}` |
| `POST /stories/sync` (scheduler token) | `POST /stories`, `PATCH /stories/{id}`, `DELETE /stories/{id}` |

Route order in `stories.py` is load-bearing: `/id/{story_id}` and `/sync` are declared **before** `/{slug}`, or FastAPI matches the literal segments as a slug.

### Substack → on-site essay sync

Essays are authored on Substack and mirrored into the `story` table, so `/essays/{slug}` is the canonical reading surface. `app/services/substack_sync.py` is the single code path — the scheduled endpoint, the backfill and the reconciler all call `upsert_entry`.

```bash
# one-shot: import the full archive (~71 posts, ~2 min at 1.5s pacing)
python backend/scripts/backfill_substack_archive.py --dry-run --limit 3   # inspect first
python backend/scripts/backfill_substack_archive.py

# ongoing: hourly via Cloud Scheduler (RSS carries only the 20 most recent)
curl -X POST $BACKEND/stories/sync -H "X-Scheduler-Token: $SCHEDULER_TOKEN"

# weekly: archive posts deleted upstream (dry-run by default)
python backend/scripts/reconcile_substack.py [--apply]
```

Four behaviours are load-bearing and were each derived from probing the live feed. Don't "simplify" them away:

1. **`/api/v1/archive` ignores `limit` above ~23.** Step `offset` by `len(response)`, never by the requested size — stepping by 50 silently yields 44 of 71 and then a convincing empty page.
2. **`content_hash` covers normalized text, not markup.** RSS emits a bare `<img>`; the JSON API emits `<picture>` + `srcset` for the same prose. Hashing markup makes the two sources disagree forever, so every hourly sync would rewrite every row.
3. **`content_source` (`api`/`rss`) stops RSS downgrading images.** On a genuine edit of an `api` row, the RSS path re-fetches the API body rather than storing RSS's poorer markup.
4. **Reconcile archives, never deletes**, uses the full archive corpus as authority (not the 20-item feed), and aborts if the corpus is empty or >10% of rows would be archived.

`source_url` (provenance, the sync's idempotency key) is deliberately distinct from `canonical_url` (SEO). Synced rows leave `canonical_url` NULL so the on-site page is canonical; `EssayDetail.tsx` prefers `canonical_url` whenever it's set, so populating both would silently de-index the essay. Remote HTML is allowlist-sanitized on ingest via `app/services/html_sanitize.py` (`nh3`) — never on render.

### Database lifecycle — important

`app.core.database.init_db()` runs on FastAPI startup and calls `SQLModel.metadata.create_all` inside a retry loop (10 attempts, exponential backoff). Alembic exists but the app currently creates tables imperatively at boot. When adding a new SQLModel, **import it inside `init_db()`** (see the explicit import block in `database.py`) or it won't be registered with `SQLModel.metadata`. Also add it to `app/models/__init__.py` so Alembic autogenerate can see it via `from app.models import *`.

### DATABASE_URL normalization

`app.core.db_url.normalize_database_url` runs at import time on the `DATABASE_URL` env var. It:
- Rewrites `postgres://` → `postgresql://`
- Injects the `+asyncpg` driver
- Converts `sslmode=` → `ssl=` (asyncpg uses `ssl`, not `sslmode`)
- Defaults to `ssl=require` unless `DB_SSL=disable` (docker-compose sets this)

Don't hand-craft the URL with `sslmode` or without `+asyncpg` — the normalizer handles it. This exists because Railway Postgres provides URLs in the psycopg format.

### Frontend layout (`frontend/src/`)

```
main.tsx             # entry — createBrowserRouter, PostHogProvider wraps RouterProvider
shell/App.tsx        # layout shell (Outlet), applied to all routes EXCEPT /links
pages/               # route components — Home, About, Archive, EssayDetail, Speak,
                     #   TopicLanding, Listen, Subscribed, Links, NotFound
pages/admin/         # Login, StoriesIndex, StoryEditor (bearer-token CRUD surface)
components/          # reusable UI + __tests__/ (vitest + Testing Library)
                     #   incl. SEO, ConsentBanner, SubscribeCTA, PillButton, SocialIconButton
hooks/               # useAnalytics, useScrollDepth
data/                # speakingTopics.mjs (+ .d.mts) — drives /speak/:topic landing pages
lib/                 # cross-cutting client utilities
  analytics.ts       #   PostHog + GA4 + Meta/TikTok pixels — all consent-gated
  schema.ts          #   JSON-LD @graph builders consumed by <SEO jsonLd={...}/>
  utm.ts             #   UTM param capture/persistence for attribution
config/api.ts        # API base URL resolution (env-aware) + endpoint map + types
config/site.ts       # site-wide branding / nav / social config
```

Routing is centralized in `main.tsx` (React Router v6 data router). Three structural rules:

- **`/links` sits outside `<App />`** — it's a bio-link landing page with no shell chrome and is intentionally hidden from nav + sitemap. Don't add it to the shell's children.
- **Retired routes redirect, they do not 404.** `/newsletter` → `/`, `/press` → `/archive`, `/contact` → `/speak`, `/essays` → `/archive`, `/admin` → `/admin/stories`. Preserve these `<Navigate replace>` entries when reshaping routes — they protect inbound link equity and ad landing pages.
- **`/essays/:slug` is canonical; `/archive/:slug` is a legacy alias.** Both render `EssayDetail`. Keep the alias — old inbound links use it — but never emit `/archive/:slug` in nav, sitemaps, or JSON-LD.

`/admin/*` renders inside `<App />` behind a bearer token stored client-side (`AdminLogin` → `/auth/login`). It is intentionally absent from nav and sitemap.

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

`config/api.ts` also exports the server-side story shapes (`StoryPublic`, `StoryDetail`, `StoryListResponse`). Keep these in sync with `app/api/schemas.py` — they're hand-mirrored, not generated.

The frontend container reads `BACKEND_URL` at boot (envsubst renders `nginx.conf.template`). In Cloud Run: `--set-env-vars BACKEND_URL=https://tih-backend-xyz.a.run.app`. In docker-compose: pinned to `http://backend:8000` in `frontend/Dockerfile` default.

New API calls should route through `API_CONFIG.endpoints` rather than hard-coding paths.

### Deployment

`cloudbuild.yaml` builds both images from the repo-root context (`-f backend/Dockerfile .` and `-f frontend/Dockerfile .`) and deploys to Cloud Run services `tih-backend` / `tih-frontend`. The Dockerfiles expect the repo root as build context. Legacy Railway support is why the DB normalizer reads `RAILWAY_PUBLIC_DOMAIN` for CORS in `main.py`.

## UI conventions (frontend)

Design system reference: **`docs/UI_DESIGN_SYSTEM.md`**. Keep it in sync when the site's visual language changes. Chronological UI-fix log: **`frontend/CHANGELOG.md`**.

Product/brand docs live in **`docs/`** (checked in). An earlier `.claude/docs/` mirror was deleted — `docs/` is the single source of truth.

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

- **Backend**: `pytest` with `pytest-asyncio`. Testpaths pinned to `backend/tests` in `pyproject.toml`. Structure: `tests/contract/` (API contract tests — auth, leads, stories, admin, substack sync, webhooks), `tests/unit/` (currently `test_html_sanitize.py`). Contract tests expect a reachable Postgres; CI runs `pytest -q || true` so failures don't block.

### ⚠ The test suite TRUNCATES its database

`backend/tests/conftest.py` has an autouse fixture that runs `TRUNCATE ... RESTART IDENTITY CASCADE` over `_TRUNCATE_TABLES` (`story`, `user`, `lead_capture`, …) **between every test**. Point it at a database holding real content and that content is gone — including the author row the Substack backfill depends on.

Use two databases on the same container:

| DB | Purpose | `DATABASE_URL` |
|---|---|---|
| `tih_db` | **tests only** — truncated constantly | `postgresql+asyncpg://postgres:postgres@localhost:5433/tih_db` |
| `tih_dev` | local dev content (the 71 synced essays) | `postgresql+asyncpg://postgres:postgres@localhost:5433/tih_dev` |

```bash
# tests — safe to wipe
DATABASE_URL='postgresql+asyncpg://postgres:postgres@localhost:5433/tih_db' pytest -q

# dev server — keeps its data
DATABASE_URL='postgresql://postgres:postgres@localhost:5433/tih_dev' \
  DB_SSL=disable SCHEDULER_TOKEN=dev-tick-token \
  uvicorn app.main:app --app-dir backend --port 8000
```

If a new model is added, add its table to `_TRUNCATE_TABLES` or rows leak between tests.
- **Frontend**: `vitest` with jsdom + Testing Library (`vitest.config.ts`, `vitest.setup.ts`). Tests live in `src/**/__tests__/`.

## CI (`.github/workflows/ci.yml`)

Two jobs on push to `main` and PRs:
- **backend**: Python 3.13, installs requirements + ruff/flake8, lints, runs pytest (non-blocking).
- **frontend**: Node 20, `npm ci`, typecheck, lint (non-blocking), test, build.

Typecheck and tests are the strict gates on the frontend; lint failures are tolerated. Keep that in mind before assuming a green CI means lint-clean.
