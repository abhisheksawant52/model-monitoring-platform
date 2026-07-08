"""Monitoring endpoints: drift checks, performance, and metrics exposition."""

from __future__ import annotations

from fastapi import APIRouter, Response
from pydantic import BaseModel, Field

from model_monitoring.config import get_settings
from model_monitoring.drift import DataDriftDetector
from model_monitoring.metrics import CONTENT_TYPE_LATEST, REGISTRY

router = APIRouter(tags=["monitoring"])


class DriftRequest(BaseModel):
    """Request payload for an on-demand data-drift check."""

    feature: str = Field(..., description="Name of the feature being evaluated.")
    reference: list[float] = Field(..., description="Reference (baseline) values.")
    current: list[float] = Field(..., description="Current (live) values.")


class DriftMetric(BaseModel):
    """A single drift metric result."""

    metric: str
    value: float
    severity: str
    drifted: bool


class DriftResponse(BaseModel):
    """Response payload for a drift check."""

    feature: str
    results: list[DriftMetric]
    drifted: bool


@router.post("/v1/drift/check", response_model=DriftResponse)
def check_drift(payload: DriftRequest) -> DriftResponse:
    """Evaluate data drift for a single feature and export metrics.

    Computes PSI and the KS statistic, records them in the Prometheus
    registry, and returns the per-metric verdict.
    """

    settings = get_settings()
    detector = DataDriftDetector(
        psi_warn=settings.psi_warn_threshold,
        psi_alert=settings.psi_alert_threshold,
    )
    results = detector.evaluate(payload.reference, payload.current)

    for result in results:
        REGISTRY.set_gauge(
            "model_monitoring_drift_score",
            result.value,
            help_text="Latest drift score by feature and metric.",
            feature=payload.feature,
            metric=result.metric,
        )

    drifted = any(r.drifted for r in results)
    return DriftResponse(
        feature=payload.feature,
        results=[
            DriftMetric(
                metric=r.metric,
                value=r.value,
                severity=r.severity.value,
                drifted=r.drifted,
            )
            for r in results
        ],
        drifted=drifted,
    )


@router.get("/metrics")
def metrics() -> Response:
    """Expose metrics in the Prometheus text exposition format."""

    return Response(content=REGISTRY.render(), media_type=CONTENT_TYPE_LATEST)
