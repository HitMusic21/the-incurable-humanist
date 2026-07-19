"""
Main FastAPI application entry point.
The Incurable Humanist - Personal Publication Platform
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api import auth, leads, newsletter, stories
from app.core.database import db_ping, init_db

# Basic logging configuration (can be overridden by server)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


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


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "The Incurable Humanist API is running"}


@app.get("/ready")
async def ready() -> Response:
    """Readiness endpoint verifying database connectivity."""
    is_db_ready = await db_ping()
    if is_db_ready:
        return Response(status_code=status.HTTP_200_OK)
    return Response(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


# Rate-limiter state (used by app.api.leads via slowapi's @limiter.limit decorators).
# Must be attached to app.state so slowapi's request middleware can find it.
app.state.limiter = leads.limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(newsletter.router, prefix="/newsletter", tags=["Newsletter"])
app.include_router(leads.router, prefix="/leads", tags=["Leads"])
app.include_router(stories.router, prefix="/stories", tags=["Stories"])

# TODO: Include other routers when implemented
# app.include_router(admin.router, prefix="/admin", tags=["Admin"])
