"""Data-drift and concept-drift detectors.

This module implements lightweight, dependency-friendly drift statistics that
are commonly used in production ML monitoring:

* **Population Stability Index (PSI)** — compares the distribution of a feature
  between a reference (training) window and a live window.
* **Kolmogorov–Smirnov (KS) statistic** — a distribution-free two-sample test
  for continuous features.
* **Concept drift** — tracks degradation in the relationship between features
  and the target by comparing rolling error rates against a baseline.

The statistics are intentionally implemented with NumPy only so the package
stays light. They are numerically reasonable but are not intended to replace a
full ``scipy.stats`` implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np
import numpy.typing as npt

ArrayLike = npt.ArrayLike


class DriftSeverity(str, Enum):
    """Severity levels for a drift assessment."""

    NONE = "none"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass(frozen=True)
class DriftResult:
    """Outcome of a single drift computation.

    Attributes:
        metric: Name of the statistic (e.g. ``"psi"`` or ``"ks"``).
        value: The computed statistic value.
        severity: Categorical severity derived from configured thresholds.
        drifted: Convenience flag, ``True`` when severity is not ``NONE``.
    """

    metric: str
    value: float
    severity: DriftSeverity
    drifted: bool


def _as_1d(values: ArrayLike) -> npt.NDArray[np.float64]:
    """Coerce ``values`` to a finite 1-D float array."""

    arr = np.asarray(values, dtype=np.float64).ravel()
    return arr[np.isfinite(arr)]


def population_stability_index(
    reference: ArrayLike,
    current: ArrayLike,
    bins: int = 10,
    epsilon: float = 1e-6,
) -> float:
    """Compute the Population Stability Index between two samples.

    PSI is defined as ``sum((c_i - r_i) * ln(c_i / r_i))`` over quantile bins,
    where ``r_i`` and ``c_i`` are the reference and current proportions in
    bin ``i``. Bin edges are derived from reference quantiles so the reference
    distribution is (approximately) uniform across bins.

    Args:
        reference: Reference (baseline) feature values.
        current: Current (live) feature values.
        bins: Number of quantile bins to use.
        epsilon: Small constant to avoid division by zero / log of zero.

    Returns:
        The PSI value. Rules of thumb: ``< 0.1`` no significant shift,
        ``0.1–0.25`` moderate shift, ``> 0.25`` major shift.
    """

    ref = _as_1d(reference)
    cur = _as_1d(current)
    if ref.size == 0 or cur.size == 0:
        return 0.0

    quantiles = np.linspace(0, 1, bins + 1)
    edges = np.unique(np.quantile(ref, quantiles))
    if edges.size < 2:
        return 0.0
    edges[0], edges[-1] = -np.inf, np.inf

    ref_counts, _ = np.histogram(ref, bins=edges)
    cur_counts, _ = np.histogram(cur, bins=edges)

    ref_prop = ref_counts / ref.size + epsilon
    cur_prop = cur_counts / cur.size + epsilon

    psi = np.sum((cur_prop - ref_prop) * np.log(cur_prop / ref_prop))
    return float(psi)


def ks_statistic(reference: ArrayLike, current: ArrayLike) -> float:
    """Compute the two-sample Kolmogorov–Smirnov statistic.

    The KS statistic is the maximum absolute difference between the empirical
    cumulative distribution functions of the two samples. It lies in
    ``[0, 1]``; larger values indicate greater divergence.

    Args:
        reference: Reference feature values.
        current: Current feature values.

    Returns:
        The KS statistic ``D``.
    """

    ref = np.sort(_as_1d(reference))
    cur = np.sort(_as_1d(current))
    if ref.size == 0 or cur.size == 0:
        return 0.0

    grid = np.concatenate([ref, cur])
    cdf_ref = np.searchsorted(ref, grid, side="right") / ref.size
    cdf_cur = np.searchsorted(cur, grid, side="right") / cur.size
    return float(np.max(np.abs(cdf_ref - cdf_cur)))


class DataDriftDetector:
    """Detect data drift for a single numeric feature.

    The detector combines PSI and the KS statistic. Severity is escalated to
    the most severe signal produced by either metric.
    """

    def __init__(
        self,
        psi_warn: float = 0.1,
        psi_alert: float = 0.25,
        ks_alert: float = 0.2,
    ) -> None:
        """Initialise the detector with severity thresholds.

        Args:
            psi_warn: PSI value at or above which a warning is raised.
            psi_alert: PSI value at or above which a critical alert is raised.
            ks_alert: KS statistic at or above which drift is flagged.
        """

        self.psi_warn = psi_warn
        self.psi_alert = psi_alert
        self.ks_alert = ks_alert

    def _psi_severity(self, psi: float) -> DriftSeverity:
        if psi >= self.psi_alert:
            return DriftSeverity.CRITICAL
        if psi >= self.psi_warn:
            return DriftSeverity.WARNING
        return DriftSeverity.NONE

    def evaluate(self, reference: ArrayLike, current: ArrayLike) -> list[DriftResult]:
        """Evaluate PSI and KS drift for one feature.

        Args:
            reference: Reference feature values.
            current: Current feature values.

        Returns:
            A list with one :class:`DriftResult` per metric.
        """

        psi = population_stability_index(reference, current)
        ks = ks_statistic(reference, current)

        psi_sev = self._psi_severity(psi)
        ks_sev = DriftSeverity.CRITICAL if ks >= self.ks_alert else DriftSeverity.NONE

        return [
            DriftResult("psi", psi, psi_sev, psi_sev is not DriftSeverity.NONE),
            DriftResult("ks", ks, ks_sev, ks_sev is not DriftSeverity.NONE),
        ]


class ConceptDriftDetector:
    """Detect concept drift via degradation of the error rate.

    Concept drift is the change in ``P(y | X)``. We approximate it by tracking
    the model's error rate over a rolling window and comparing it to a baseline
    error rate captured on the reference dataset. A relative increase beyond
    ``tolerance`` is treated as drift.
    """

    def __init__(self, baseline_error_rate: float, tolerance: float = 0.25) -> None:
        """Initialise the detector.

        Args:
            baseline_error_rate: Error rate observed on the reference dataset.
            tolerance: Relative increase in error rate that triggers an alert
                (``0.25`` means a 25% relative degradation).
        """

        self.baseline_error_rate = max(baseline_error_rate, 1e-6)
        self.tolerance = tolerance

    def evaluate(self, y_true: ArrayLike, y_pred: ArrayLike) -> DriftResult:
        """Assess concept drift from recent predictions.

        Args:
            y_true: Ground-truth labels for the live window.
            y_pred: Model predictions for the live window.

        Returns:
            A :class:`DriftResult` with metric ``"concept_error_ratio"``.
        """

        truth = np.asarray(y_true).ravel()
        pred = np.asarray(y_pred).ravel()
        if truth.size == 0:
            return DriftResult("concept_error_ratio", 0.0, DriftSeverity.NONE, False)

        current_error = float(np.mean(truth != pred))
        ratio = current_error / self.baseline_error_rate
        drifted = ratio >= (1.0 + self.tolerance)
        severity = DriftSeverity.CRITICAL if drifted else DriftSeverity.NONE
        return DriftResult("concept_error_ratio", ratio, severity, drifted)
