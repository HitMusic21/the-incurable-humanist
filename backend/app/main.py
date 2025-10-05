"""
Main FastAPI application entry point.
The Incurable Humanist - Personal Publication Platform
"""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import auth, newsletter
from app.core.database import db_ping

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup: Do not block on database connection
    logger.info("Starting application...")
    logger.info("Application startup complete (DB connection not required for startup)")
    yield
    # Shutdown: cleanup if needed
    logger.info("Application shutting down...")


app = FastAPI(
    title="The Incurable Humanist API",
    description="Personal publication platform for Denise Rodriguez Dao",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration for frontend
import os
allowed_origins = [
    "http://localhost:5173",  # Vite dev server
    "https://theincurablehumanist.com",
    "https://www.theincurablehumanist.com",
]
# Add Railway frontend URL if deployed
railway_url = os.getenv("RAILWAY_PUBLIC_DOMAIN")
if railway_url:
    allowed_origins.append(f"https://{railway_url}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """
    Liveness check endpoint (no DB dependency).
    Used by Railway for liveness checks - MUST NOT query database.
    """
    return {"ok": True}


@app.get("/ready")
async def ready():
    """
    Readiness check endpoint with database connectivity verification.
    Used by Railway for readiness checks before routing traffic.
    """
    return {"db": await db_ping()}


@app.get("/api")
async def api_root():
    """API root endpoint."""
    return {
        "message": "The Incurable Humanist API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "ready": "/ready"
    }


# Include API routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(newsletter.router, prefix="/api/newsletter", tags=["Newsletter"])

# TODO: Include other routers when implemented
# app.include_router(stories.router, prefix="/api/stories", tags=["Stories"])
# app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])

# Serve static frontend files (production only)
# In production, the frontend is built and available in frontend/dist
frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    # Mount API routes first, then catch-all static files
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static")
