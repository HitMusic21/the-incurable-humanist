# Deploying to Railway

## Backend (FastAPI)
- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check: `GET /` should return JSON message
- Env vars:
  - `RAILWAY_PUBLIC_DOMAIN` is auto-provided; CORS is configured to allow it
  - Add your DB or API keys as needed
- Optional: `backend/Procfile` already provides the start command.

## Frontend (Vite static site)
- Root directory: `frontend`
- Build command: `npm ci && npm run build`
- Output directory: `dist`
- No start command needed for static site; use Railway Static Sites.

## Steps (UI)
1. Create two services in your project: one for `backend`, one Static Site for `frontend`.
2. For the backend service:
   - Set Root to `backend`
   - Build command and Start command as above (or use Procfile)
3. For the frontend service:
   - Set Root to `frontend`
   - Build command and Output directory as above
4. Add environment variables as needed. Redeploy.
