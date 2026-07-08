"""Liveness and readiness probe endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from model_monitoring import __version__

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Health/readiness response payload."""

    status: str
    version: str


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness probe: the process is up and serving requests."""

    return HealthResponse(status="ok", version=__version__)


@router.get("/ready", response_model=HealthResponse)
def ready() -> HealthResponse:
    """Readiness probe: dependencies are wired and traffic may be routed."""

    return HealthResponse(status="ready", version=__version__)
