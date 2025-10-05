"""
Main FastAPI application entry point.
The Incurable Humanist - Personal Publication Platform
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "The Incurable Humanist API is running"}


# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(newsletter.router, prefix="/newsletter", tags=["Newsletter"])

# TODO: Include other routers when implemented
# app.include_router(stories.router, prefix="/stories", tags=["Stories"])
# app.include_router(admin.router, prefix="/admin", tags=["Admin"])
