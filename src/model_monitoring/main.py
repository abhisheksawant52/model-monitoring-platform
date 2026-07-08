"""FastAPI application factory and entrypoint.

Run locally with::

    uvicorn model_monitoring.main:app --reload

or via the installed console script ``model-monitoring``.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from model_monitoring import __version__
from model_monitoring.api import health_router, monitoring_router
from model_monitoring.config import get_settings
from model_monitoring.logging_config import configure_logging, get_logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Configure logging on startup and log shutdown."""

    settings = get_settings()
    configure_logging(settings.log_level)
    logger = get_logger(__name__)
    logger.info("Starting %s v%s (%s)", settings.app_name, __version__, settings.environment)
    yield
    logger.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""

    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="Data-drift, concept-drift and performance monitoring for ML models.",
        lifespan=lifespan,
    )
    app.include_router(health_router)
    app.include_router(monitoring_router)
    return app


app = create_app()


def main() -> None:
    """Console-script entrypoint that serves the app with uvicorn."""

    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "model_monitoring.main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
