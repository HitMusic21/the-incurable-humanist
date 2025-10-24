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
- Backend: set `DATABASE_URL`, `SENDGRID_API_KEY`, etc.
  ```bash
gcloud run services update tih-backend \
  --region us-central1 \
  --set-env-vars DATABASE_URL="postgresql+asyncpg://..." \
  --set-env-vars PYTHONUNBUFFERED=1
```

## Local Development with Docker Compose
```bash
docker compose up --build
```

## Notes
- Frontend uses `frontend/nginx.conf` to support SPA routing on Cloud Run (listen 8080).
- Backend exposes uvicorn on port 8080 by default in Cloud Run.
