# Railway Deployment Checklist

## ✅ Pre-Deployment Preparation Complete

### Configuration Files Created
- ✅ `Procfile` - Railway start command
- ✅ `railway.json` - Build and deploy configuration
- ✅ `nixpacks.toml` - Nixpacks build instructions
- ✅ `.railwayignore` - Files to exclude from deployment

### Code Updates
- ✅ Added Redis and aiofiles to `backend/requirements.txt`
- ✅ Updated API routes to `/api/*` prefix in `backend/app/main.py`
- ✅ Added static file serving for frontend in `backend/app/main.py`
- ✅ Updated CORS to allow production domains
- ✅ Added `/health` endpoint for Railway health checks
- ✅ Updated frontend API config to detect production environment

---

## 🚀 Railway Deployment Steps

### 1. Add Services in Railway Dashboard

#### a. PostgreSQL Database
1. Click "New" → "Database" → "Add PostgreSQL"
2. Railway will auto-generate `DATABASE_URL`
3. ✅ No additional configuration needed

#### b. Redis Cache
1. Click "New" → "Database" → "Add Redis"
2. Railway will auto-generate `REDIS_URL`
3. ✅ No additional configuration needed

### 2. Set Required Environment Variables

In Railway project settings, add these variables:

```bash
# Application Security (REQUIRED)
SECRET_KEY=<generate-with-command-below>

# Application Configuration (REQUIRED)
AUTHOR_EMAIL=denise@theincurablehumanist.com
FRONTEND_URL=https://theincurablehumanist.com

# Auto-provided by Railway (DO NOT SET MANUALLY)
DATABASE_URL=<auto-provided-by-postgresql-plugin>
REDIS_URL=<auto-provided-by-redis-plugin>
PORT=<auto-provided-by-railway>
RAILWAY_PUBLIC_DOMAIN=<auto-provided-by-railway>
```

**Generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Deploy from GitHub

```bash
# Commit all changes
git add .
git commit -m "Configure Railway deployment"
git push origin main
```

In Railway:
1. Connect your GitHub repository
2. Select the branch (main/master)
3. Railway will automatically detect configuration and deploy

### 4. Configure Custom Domain (Optional)

1. In Railway project settings → Domains
2. Add custom domain: `theincurablehumanist.com`
3. Update DNS records as instructed by Railway:
   - Add CNAME or A record pointing to Railway
4. Wait for DNS propagation (up to 24 hours)

---

## 🔍 Post-Deployment Verification

### Health Checks
```bash
# Check API health
curl https://your-railway-domain.up.railway.app/health

# Expected response:
{
  "status": "healthy",
  "service": "The Incurable Humanist API",
  "version": "1.0.0"
}
```

### API Endpoints
```bash
# Test API root
curl https://your-railway-domain.up.railway.app/api

# Test newsletter endpoint
curl https://your-railway-domain.up.railway.app/api/newsletter/articles
```

### Frontend
- Visit `https://your-railway-domain.up.railway.app/`
- Should see React app homepage
- Check that all pages load correctly
- Verify analytics tracking (Google Analytics, Meta Pixel, PostHog)

---

## 📁 Project Structure (Deployed)

```
TIH2/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app + static file serving
│   │   ├── api/             # API routes (now under /api/*)
│   │   └── core/            # Database, config
│   └── requirements.txt     # Python dependencies (includes redis, aiofiles)
│
├── frontend/
│   ├── dist/                # Built frontend (served by FastAPI)
│   └── src/
│       └── config/
│           └── api.ts       # Auto-detects prod vs dev environment
│
├── Procfile                 # Start command
├── railway.json             # Railway config
├── nixpacks.toml            # Build configuration
└── .railwayignore           # Deployment exclusions
```

---

## 🐛 Troubleshooting

### Build Fails
**Error:** "No module named 'app'"
- ✅ Fixed: Start command uses `cd backend && uvicorn app.main:app`

**Error:** Frontend build fails
- Check `frontend/package.json` scripts
- Ensure `npm run build` works locally

### Runtime Errors
**CORS errors in browser**
- Verify production domain in CORS allowed_origins
- Check RAILWAY_PUBLIC_DOMAIN is set

**Database connection errors**
- Verify DATABASE_URL format: `postgresql+asyncpg://...`
- Ensure PostgreSQL plugin is connected

**Static files not loading**
- Verify `frontend/dist/` exists after build
- Check FastAPI StaticFiles mount is after API routes

### API Routes 404
- All API endpoints now use `/api/` prefix
- Update any frontend calls to use new paths
- Health check is at `/health` (no /api prefix)

---

## 🔄 Future Updates

To deploy new changes:

```bash
git add .
git commit -m "Your changes"
git push origin main
```

Railway will automatically:
1. Pull latest code
2. Rebuild frontend (`npm run build`)
3. Reinstall dependencies
4. Restart the application

---

## 🔐 Security Notes

### Environment Variables
- ✅ Never commit `.env` files
- ✅ Use Railway environment variables
- ✅ Rotate SECRET_KEY periodically

### CORS Configuration
Current allowed origins:
- `http://localhost:5173` (dev)
- `https://theincurablehumanist.com`
- `https://www.theincurablehumanist.com`
- Railway public domain (auto-added)

### Database
- ✅ PostgreSQL uses SSL by default on Railway
- ✅ Credentials auto-generated and rotated by Railway

---

## 📊 Monitoring & Analytics

**Built-in Analytics:**
- Google Analytics: `G-E0YFH2FWLN`
- Meta Pixel: `809214198133257`
- PostHog: Custom event tracking

**Railway Monitoring:**
- View logs in Railway dashboard
- Monitor resource usage (CPU, memory)
- Set up alerts for downtime

**Health Endpoint:**
- `/health` - Basic health check
- Can be extended to check database connectivity, Redis, etc.

---

## ✨ What's Different from Development

| Feature | Development | Production |
|---------|------------|------------|
| API Base URL | `http://localhost:8000` | Same domain (empty string) |
| API Routes | `/auth/*`, `/newsletter/*` | `/api/auth/*`, `/api/newsletter/*` |
| Frontend | Vite dev server (port 5173) | Built static files served by FastAPI |
| Database | Docker PostgreSQL (localhost:5433) | Railway PostgreSQL |
| Redis | Docker Redis | Railway Redis |
| CORS | Only localhost | Production domains + Railway domain |
| Environment | `.env` file | Railway environment variables |

---

## 🎉 You're Ready to Deploy!

All configuration is complete. Follow the deployment steps above to launch on Railway.

**Quick Start:**
1. Add PostgreSQL and Redis plugins in Railway
2. Set SECRET_KEY environment variable
3. Push to GitHub
4. Railway deploys automatically

Need help? Check Railway logs or the troubleshooting section above.
