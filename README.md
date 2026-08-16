# The Incurable Humanist

A personal publication platform for the writer Denise Rodriguez Dao — essays, an
archive, speaking pages, and newsletter lead capture.

- **Backend** — FastAPI (async), SQLModel, PostgreSQL
- **Frontend** — React 18 + TypeScript, Vite, Tailwind CSS
- **Deploy** — two containers on Google Cloud Run, built by Cloud Build

## Quickstart

Backend and frontend run independently; you need both for the full app.

```bash
# Backend (from repo root)
source backend/venv/bin/activate
make be-install
make be-run          # uvicorn on :8000

# Frontend (from repo root, second shell)
make fe-install
make fe-dev          # vite dev server on :5173
```

Or bring the whole stack up in Docker:

```bash
docker compose up --build
```

`docker-compose.override.yml` remaps host ports to avoid colliding with the
native dev servers — see CLAUDE.md for the current mapping.

## Checks

```bash
make lint    # be-lint (ruff + flake8) + fe-lint (eslint)
make test    # be-test (pytest) + fe-test (vitest)
```

The individual targets — `be-lint`, `be-test`, `be-format`, `fe-lint`,
`fe-test`, `fe-typecheck`, `fe-build` — are all in the `Makefile`.

## Layout

```
backend/     FastAPI app (app/api, app/services, app/core, app/models), tests, Alembic
frontend/    React SPA — see frontend/README.md
docs/        Product and brand docs, incl. UI_DESIGN_SYSTEM.md
specs/       Feature specs
cloudbuild.yaml   Cloud Build pipeline for both images
```

## Where to go next

- **[CLAUDE.md](./CLAUDE.md)** — architecture, conventions, and the non-obvious
  rules (database lifecycle, `DATABASE_URL` normalization, consent-gated
  analytics, UI conventions). Authoritative reference.
- **[GCP_DEPLOYMENT.md](./GCP_DEPLOYMENT.md)** — Cloud Run deployment and
  environment variables.
- **[frontend/README.md](./frontend/README.md)** — frontend specifics.
