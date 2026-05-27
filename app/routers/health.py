"""
health.py — Health check endpoints.

WHY DO WE NEED HEALTH CHECKS?
- Kubernetes / Docker use /health to know if the container is alive
- Load balancers route traffic away from unhealthy instances
- Monitoring tools (Datadog, Grafana) ping this every 30s
- Developers can verify the server is running correctly

TWO COMMON PATTERNS:
  /health  → "Is the server running?" (liveness probe)
  /ready   → "Is the server ready to serve traffic?" (readiness probe)
"""

from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter(prefix="/health", tags=["Health"])


# ── Response Models ───────────────────────────────────────────
class HealthResponse(BaseModel):
    """Structured response for health check"""

    status: str
    app_name: str
    version: str
    environment: str
    timestamp: str


class ReadinessResponse(BaseModel):
    """Readiness check - includes dependency status."""

    status: str
    app_name: str
    version: str
    environment: str
    timestamp: str
    dependencies: dict[str, str]


# ── Endpoints ───────────────────────────────────────────────────────────
@router.get(
    "/",
    response_model=HealthResponse,
    summary="Liveness Check",
    description="Returns 200 if the server is running. Used by Developer/Docker/K8s",
)
async def health_check() -> HealthResponse:
    """
    Liveness probe - answer: 'Is the process alive?'
    Should NEVER fail unless the server itselfcrashed.
    """
    return HealthResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness Check",
    description="Returns status of all dependencies (DB, Redis, LLM).",
)
async def readiness_check() -> ReadinessResponse:
    """
     Readiness probe — answers: 'Can the app serve real traffic?'

    In Phase 1, we just return placeholders.
    In Phase 6+, we'll actually ping DB and Redis here.
    """
    # Phase 1: Mocked — will be replaced with real checks in later phases
    dependencies = {
        "groq_llm": "not_configured",  # Phase 2
        "postgresql": "not_configured",  # Phase 6
        "redis": "not_configured",  # Phase 7
    }

    # Determine overall readiness
    # For now: always ready since no real deps yet
    overall_status = "ready"

    return ReadinessResponse(
        status=overall_status,
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
        timestamp=datetime.now(timezone.utc).isoformat(),
        dependencies=dependencies,
    )
