"""API routers for the model-monitoring service."""

from __future__ import annotations

from model_monitoring.api.health import router as health_router
from model_monitoring.api.monitoring import router as monitoring_router

__all__ = ["health_router", "monitoring_router"]
