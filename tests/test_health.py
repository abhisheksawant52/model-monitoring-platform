"""Tests for the health and readiness endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from model_monitoring.main import app

client = TestClient(app)


def test_health_ok() -> None:
    """/health returns 200 with an ok status."""

    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body


def test_ready_ok() -> None:
    """/ready returns 200 with a ready status."""

    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_metrics_exposition() -> None:
    """/metrics returns Prometheus-formatted text."""

    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
