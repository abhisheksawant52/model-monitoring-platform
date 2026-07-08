"""Unit tests for the drift detectors using tiny in-memory arrays."""

from __future__ import annotations

import numpy as np

from model_monitoring.drift import (
    ConceptDriftDetector,
    DataDriftDetector,
    DriftSeverity,
    ks_statistic,
    population_stability_index,
)


def test_psi_zero_for_identical_distributions() -> None:
    """PSI is ~0 when reference and current are the same sample."""

    data = np.arange(0, 100, dtype=float)
    assert population_stability_index(data, data) < 0.01


def test_psi_large_for_shifted_distribution() -> None:
    """A clearly shifted distribution yields a large PSI."""

    reference = np.arange(0, 100, dtype=float)
    current = np.arange(200, 300, dtype=float)
    assert population_stability_index(reference, current) > 0.25


def test_ks_bounds() -> None:
    """KS statistic is 0 for identical data and near 1 for disjoint data."""

    ref = np.arange(0, 50, dtype=float)
    assert ks_statistic(ref, ref) == 0.0
    assert ks_statistic(ref, ref + 1000) > 0.9


def test_data_drift_detector_flags_shift() -> None:
    """The detector reports critical severity on a strong shift."""

    detector = DataDriftDetector()
    results = detector.evaluate(np.arange(0, 100.0), np.arange(500, 600.0))
    assert any(r.drifted for r in results)
    assert any(r.severity is DriftSeverity.CRITICAL for r in results)


def test_concept_drift_detector() -> None:
    """Concept drift fires when the live error rate degrades past tolerance."""

    detector = ConceptDriftDetector(baseline_error_rate=0.1, tolerance=0.25)
    y_true = np.array([0, 1, 0, 1, 0, 1, 0, 1, 0, 1])
    y_pred = np.array([1, 0, 1, 0, 1, 0, 1, 0, 1, 0])  # all wrong -> error 1.0
    result = detector.evaluate(y_true, y_pred)
    assert result.drifted
    assert result.value > 1.25
