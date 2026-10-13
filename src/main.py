"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.config import settings
from src.db import init_db, close_db, get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app lifecycle (startup/shutdown)."""
    # Startup
    await init_db(settings.DATABASE_URL)
    db = get_db()
    is_healthy = await db.health_check()
    if not is_healthy:
        raise RuntimeError("Failed to connect to database")
    print("✅ Database connected")

    yield

    # Shutdown
    await close_db()
    print("✅ Database disconnected")


app = FastAPI(
    title="URL Shortener API",
    description="Fast, simple URL shortening service",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """Health check endpoint (K8s liveness probe)."""
    db = get_db()
    is_healthy = await db.health_check()
    status = "healthy" if is_healthy else "unhealthy"
    return {"status": status, "service": "url-shortener"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "URL Shortener API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }
