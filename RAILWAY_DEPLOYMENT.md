# Railway Deployment Guide

## Prerequisites

Your TIH2 application is now configured for Railway deployment with:
- `Procfile` - Railway start command
- `railway.json` - Railway build and deploy configuration
- `nixpacks.toml` - Nixpacks build configuration
- Updated CORS in `backend/app/main.py` to support production domains

## Required Environment Variables

Set these in your Railway project settings:

### Database
```
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DATABASE
```
**Note:** Railway provides PostgreSQL - add the PostgreSQL plugin and use the connection string it provides.

### Redis (Cache/Sessions)
```
REDIS_URL=redis://USER:PASSWORD@HOST:PORT
```
**Note:** Railway provides Redis - add the Redis plugin and use the connection string it provides.

### Application Secrets
```
SECRET_KEY=<generate-a-secure-random-key>
```
Generate a secure key with:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Application Configuration
```
AUTHOR_EMAIL=denise@theincurablehumanist.com
FRONTEND_URL=https://theincurablehumanist.com
```

### Optional (Auto-provided by Railway)
```
PORT=<auto-provided-by-railway>
RAILWAY_PUBLIC_DOMAIN=<auto-provided-by-railway>
```

## Deployment Steps

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Add Railway deployment configuration"
   git push origin main
   ```

2. **In Railway Dashboard:**
   - Create a new project
   - Connect your GitHub repository
   - Add PostgreSQL plugin (Database)
   - Add Redis plugin (Cache/Sessions)
   - Set environment variables listed above (DATABASE_URL and REDIS_URL will be auto-populated)
   - Deploy!

3. **Post-Deployment:**
   - Railway will automatically detect the configuration
   - Backend API will be available at your Railway domain
   - Frontend is built and served from the backend

## Project Structure

```
TIH2/
├── backend/          # FastAPI backend (deployed)
│   ├── app/
│   │   └── main.py  # App entry point
│   └── requirements.txt
├── frontend/         # React frontend (built & served)
│   ├── src/
│   └── package.json
├── Procfile         # Railway start command
├── railway.json     # Railway configuration
└── nixpacks.toml    # Nixpacks build config
```

## Troubleshooting

### Database Connection Issues
- Ensure DATABASE_URL uses `postgresql+asyncpg://` scheme
- Verify PostgreSQL plugin is added and connected

### CORS Errors
- Check that your production domain is added to CORS allowed origins in `backend/app/main.py`
- Verify RAILWAY_PUBLIC_DOMAIN is set correctly

### Build Failures
- Check that both `backend/requirements.txt` and `frontend/package.json` are valid
- Review Railway build logs for specific errors

## Static Frontend Serving

Currently, the frontend is built but not served by the backend. To serve the frontend from FastAPI:

1. Add to `backend/app/main.py`:
```python
from fastapi.staticfiles import StaticFiles

# After defining routes, add:
app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="static")
```

2. This will serve the React app from the FastAPI backend at the root URL.

## Custom Domain

To use `theincurablehumanist.com`:
1. Go to Railway project settings
2. Add custom domain
3. Update DNS records as instructed by Railway
4. Update FRONTEND_URL environment variable
