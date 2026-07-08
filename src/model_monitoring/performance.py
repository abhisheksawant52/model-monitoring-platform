"""Rolling model-performance metrics.

Tracks classification quality (accuracy, precision, recall) and serving
latency over a bounded rolling window so the service can surface live
degradation without retaining unbounded history.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt


@dataclass(frozen=True)
class PerformanceSnapshot:
    """A point-in-time view of model performance over the window."""

    samples: int
    accuracy: float
    precision: float
    recall: float
    latency_p50_ms: float
    latency_p95_ms: float


class RollingPerformanceTracker:
    """Maintain rolling classification and latency metrics.

    Predictions and latencies are appended as they arrive; the oldest entries
    are evicted once ``window`` is exceeded. All metrics assume binary labels
    where ``1`` is the positive class.
    """

    def __init__(self, window: int = 1000) -> None:
        """Initialise the tracker.

        Args:
            window: Maximum number of observations to retain.
        """

        self.window = window
        self._y_true: deque[int] = deque(maxlen=window)
        self._y_pred: deque[int] = deque(maxlen=window)
        self._latencies: deque[float] = deque(maxlen=window)

    def observe(self, y_true: int, y_pred: int, latency_ms: float) -> None:
        """Record a single prediction outcome.

        Args:
            y_true: Ground-truth binary label.
            y_pred: Predicted binary label.
            latency_ms: Inference latency in milliseconds.
        """

        self._y_true.append(int(y_true))
        self._y_pred.append(int(y_pred))
        self._latencies.append(float(latency_ms))

    def observe_batch(
        self,
        y_true: npt.ArrayLike,
        y_pred: npt.ArrayLike,
        latencies_ms: npt.ArrayLike,
    ) -> None:
        """Record a batch of prediction outcomes."""

        for yt, yp, lat in zip(
            np.asarray(y_true).ravel(),
            np.asarray(y_pred).ravel(),
            np.asarray(latencies_ms).ravel(),
            strict=True,
        ):
            self.observe(int(yt), int(yp), float(lat))

    def snapshot(self) -> PerformanceSnapshot:
        """Compute current metrics over the retained window."""

        if not self._y_true:
            return PerformanceSnapshot(0, 0.0, 0.0, 0.0, 0.0, 0.0)

        y_true = np.array(self._y_true)
        y_pred = np.array(self._y_pred)
        latencies = np.array(self._latencies)

        accuracy = float(np.mean(y_true == y_pred))

        true_pos = float(np.sum((y_pred == 1) & (y_true == 1)))
        pred_pos = float(np.sum(y_pred == 1))
        actual_pos = float(np.sum(y_true == 1))

        precision = true_pos / pred_pos if pred_pos else 0.0
        recall = true_pos / actual_pos if actual_pos else 0.0

        return PerformanceSnapshot(
            samples=int(y_true.size),
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            latency_p50_ms=float(np.percentile(latencies, 50)),
            latency_p95_ms=float(np.percentile(latencies, 95)),
        )
