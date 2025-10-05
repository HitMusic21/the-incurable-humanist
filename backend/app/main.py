"""
Main FastAPI application entry point.
The Incurable Humanist - Personal Publication Platform
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import auth, newsletter
from app.core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup: Initialize database
    await init_db()
    yield
    # Shutdown: cleanup if needed


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
async def health_check():
    """Health check endpoint for Railway and monitoring."""
    return {
        "status": "healthy",
        "service": "The Incurable Humanist API",
        "version": "1.0.0"
    }


@app.get("/api")
async def api_root():
    """API root endpoint."""
    return {
        "message": "The Incurable Humanist API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
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
