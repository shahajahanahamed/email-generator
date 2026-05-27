"""
main.py — FastAPI application entry point.

This is the heart of your server. It:
  1. Creates the FastAPI app instance
  2. Registers all routers (health, email, etc.)
  3. Handles startup/shutdown lifecycle events
  4. Configures CORS, middleware, error handling
"""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import desc

from app.core.config import settings
from app.routers import health

# ── Logging Setup ──────────────────────────────────────────────
# Configure before anything else so startup logs are captured
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

# ── Lifespan Manager ───────────────────────────────────────────
# Modern FastAPI pattern (replaces @app.on_event which is deprecated)
# Everting BEFORE yield = startup
# Everything AFTER yield = shutdown


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the full lifecycle of the application.

    Startup tasks (before yield):
      - Connect to database
      - Connect to Redis
      - Warm up LLM client
      - Load configuration

    Shutdown tasks (after yield):
      - Close DB connections
      - Flush Redis buffers
      - Clean up resources

      Phase 1: Just logs. Real connections added in Phase 6+.

    """
    # ── STARTUP ────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info(f"  Starting: {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"  Environment: {settings.APP_ENV}")
    logger.info(f"  Debug mode: {settings.DEBUG}")
    logger.info("=" * 60)

    # Phase 2: Initialize Groq LLM client
    # Phase 6: Initialize PostgreSQL connection pool
    # Phase 7: Initialize Redis connection

    logger.info("✅ Application startup complete")

    yield  # ← Application runs here (handles requests)

    # ── SHUTDOWN ───────────────────────────────────────────
    logger.info("🛑 Shutting down application...")

    # Phase 6: await db.disconnect()
    # Phase 7: await redis.close()

    logger.info("✅ Shutdown complete")


# ── FastAPI App Instance ────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    ## AI Email Generator API

    Generate professional emails from bullet points using AI.

    ### Features
    - 🤖 AI-powered email generation (Groq + Llama 3.1)
    - 🎨 Multiple tones (formal, casual, friendly, assertive)
    - 📝 Template support (sales, HR, support, marketing)
    - 🌍 Multi-language support
    - 📊 Email history & analytics
    - ⚡ Redis caching for performance

    ### Phases
    - **Phase 1**: Project setup ✅
    - **Phase 2**: Basic generation (coming next)
    - **Phase 3+**: Advanced features
    """,
    docs_url="/docs",  # Swagger UI at /docs
    redoc_url="/redoc",  # ReDoc UI at /redoc
    lifespan=lifespan,
)

# ── CORS Middleware ────────────────────────────────────────────────────────────
# Allows your frontend (React, Vue, etc.) to call this API
# In production: replace "*" with your actual frontend domain

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Register Routers ───────────────────────────────────────────────────────────
# Each router handles a feature domain
# Phase 2 will add: app.include_router(email.router)

app.include_router(health.router)


# ── Root Endpoint ──────────────────────────────────────────────────────────────


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint — quick sanity check.
    Returns API info and links to documentation.
    """
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "docs": "/docs",
        "health": "/health",
        "status": "Phase 1 complete ✅",
    }
