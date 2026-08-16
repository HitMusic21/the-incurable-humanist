# Deploying to Google Cloud

## Prerequisites
- gcloud CLI authenticated (gcloud auth login)
- Project set: `gcloud config set project <PROJECT_ID>`
- Enable APIs: Cloud Run, Cloud Build, Artifact Registry

## Services
- Backend: FastAPI on Cloud Run (port 8080)
- Frontend: Static SPA served by nginx on Cloud Run (port 8080)

## Build & Deploy with Cloud Build
Create a trigger on GitHub repo pointing to `cloudbuild.yaml`. Substitutions:
- `_REGION`: e.g. `us-central1`
- `_SERVICE_BACKEND`: e.g. `tih-backend`
- `_SERVICE_FRONTEND`: e.g. `tih-frontend`
- `_REPO_NAME`: `the-incurable-humanist`

Manual run:
```bash
gcloud builds submit --config cloudbuild.yaml --substitutions=_REGION=us-central1,_SERVICE_BACKEND=tih-backend,_SERVICE_FRONTEND=tih-frontend,_REPO_NAME=the-incurable-humanist
```

## Environment Variables

> **Use `--update-env-vars`, not `--set-env-vars`.** `--set-env-vars` REPLACES the
> service's entire env var set, so a second call silently drops everything the
> first one configured. Two `--set-env-vars` flags in one command is the same bug:
> only the last wins.

- Backend: set `DATABASE_URL`, `SENDGRID_API_KEY`, etc.
  ```bash
gcloud run services update tih-backend \
  --region us-central1 \
  --update-env-vars DATABASE_URL="postgresql+asyncpg://...",PYTHONUNBUFFERED=1
```

`cloudbuild.yaml` sets `PYTHONUNBUFFERED` and `AUTHOR_EMAIL` on every deploy (via
`--update-env-vars`, so it merges rather than clobbering the values above) and
mounts `SCHEDULER_TOKEN` from Secret Manager.

## Substack sync — one-time setup

`POST /stories/sync` mirrors Substack essays into the `story` table. It **fails
closed**: with no `SCHEDULER_TOKEN` it returns 503 and syncs nothing, so these
steps are required before the sync will ever run.

**1. Create the scheduler token secret** (referenced by `cloudbuild.yaml`):

```bash
openssl rand -hex 32 | gcloud secrets create tih-scheduler-token --data-file=-

# let the Cloud Run service account read it
PROJECT_NUMBER=$(gcloud projects describe "$(gcloud config get-value project)" --format='value(projectNumber)')
gcloud secrets add-iam-policy-binding tih-scheduler-token \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role=roles/secretmanager.secretAccessor
```

**2. Create the author row.** The sync attributes essays to `AUTHOR_EMAIL` and
refuses to run if that user is missing or has `is_author=false` — it never
auto-creates one. Register via `POST /auth/register`, then set the flag on the
production database.

**3. Backfill the archive once** (RSS only carries the 20 most recent posts):

```bash
DATABASE_URL="postgresql+asyncpg://..." python backend/scripts/backfill_substack_archive.py --dry-run --limit 3
DATABASE_URL="postgresql+asyncpg://..." python backend/scripts/backfill_substack_archive.py
```

**4. Schedule the hourly sync:**

```bash
gcloud scheduler jobs create http tih-substack-sync \
  --location us-central1 \
  --schedule "0 * * * *" \
  --uri "https://<tih-backend-url>/stories/sync" \
  --http-method POST \
  --headers "X-Scheduler-Token=$(gcloud secrets versions access latest --secret=tih-scheduler-token)" \
  --attempt-deadline 300s
```

The endpoint is idempotent — a run with nothing new returns
`{"created":0,"updated":0,"skipped":20}` and writes nothing, so retries and
overlapping runs are safe.

**5. Optional weekly reconcile** — archives essays deleted upstream. Dry-run by
default; aborts if the upstream corpus is empty or more than 10% of rows would be
archived:

```bash
DATABASE_URL="postgresql+asyncpg://..." python backend/scripts/reconcile_substack.py [--apply]
```

## Local Development with Docker Compose
```bash
docker compose up --build
```

## Notes
- Frontend uses `frontend/nginx.conf` to support SPA routing on Cloud Run (listen 8080).
- Backend exposes uvicorn on port 8080 by default in Cloud Run.
