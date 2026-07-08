"""Reference dataset (baseline) management.

A *baseline* captures the statistical profile of the data and model behaviour
at training/validation time. Drift detectors compare live traffic against the
active baseline. Baselines are persisted to object storage (S3) as JSON so
they can be versioned and shared across replicas.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

import numpy as np
import numpy.typing as npt


@dataclass
class FeatureBaseline:
    """Summary statistics for a single numeric feature."""

    name: str
    mean: float
    std: float
    quantiles: list[float]
    sample_count: int


@dataclass
class Baseline:
    """A versioned reference profile for a model.

    Attributes:
        model_name: Logical name of the monitored model.
        version: Baseline version identifier.
        created_at: ISO-8601 creation timestamp (UTC).
        baseline_error_rate: Error rate observed on the reference dataset.
        features: Per-feature summary statistics.
    """

    model_name: str
    version: str
    baseline_error_rate: float
    features: dict[str, FeatureBaseline] = field(default_factory=dict)
    created_at: str = field(
        default_factory=lambda: datetime.now(tz=timezone.utc).isoformat()
    )

    def to_json(self) -> str:
        """Serialise the baseline to a JSON string."""

        return json.dumps(asdict(self), default=str)

    @classmethod
    def from_json(cls, blob: str) -> Baseline:
        """Deserialise a baseline from a JSON string."""

        data = json.loads(blob)
        features = {
            name: FeatureBaseline(**feat) for name, feat in data.pop("features", {}).items()
        }
        return cls(features=features, **data)


def build_feature_baseline(
    name: str, values: npt.ArrayLike, quantile_points: int = 10
) -> FeatureBaseline:
    """Compute summary statistics for a feature column.

    Args:
        name: Feature name.
        values: Reference values for the feature.
        quantile_points: Number of evenly spaced quantiles to store.

    Returns:
        A populated :class:`FeatureBaseline`.
    """

    arr = np.asarray(values, dtype=np.float64).ravel()
    arr = arr[np.isfinite(arr)]
    qs = np.linspace(0, 1, quantile_points + 1)
    quantiles = np.quantile(arr, qs).tolist() if arr.size else []
    return FeatureBaseline(
        name=name,
        mean=float(arr.mean()) if arr.size else 0.0,
        std=float(arr.std()) if arr.size else 0.0,
        quantiles=quantiles,
        sample_count=int(arr.size),
    )


class BaselineStore:
    """Persist and retrieve baselines from an S3 bucket.

    The boto3 S3 client is injected to keep the class importable and unit
    testable without AWS credentials. Keys are laid out as
    ``{prefix}{model_name}/{version}.json``.
    """

    def __init__(self, bucket: str, prefix: str = "baselines/", client: object | None = None):
        self.bucket = bucket
        self.prefix = prefix
        self._client = client

    def _key(self, model_name: str, version: str) -> str:
        return f"{self.prefix}{model_name}/{version}.json"

    def save(self, baseline: Baseline) -> str:
        """Persist ``baseline`` and return its S3 key."""

        key = self._key(baseline.model_name, baseline.version)
        if self._client is None:  # pragma: no cover - requires AWS at runtime
            raise RuntimeError("BaselineStore has no S3 client configured")
        self._client.put_object(  # type: ignore[attr-defined]
            Bucket=self.bucket,
            Key=key,
            Body=baseline.to_json().encode("utf-8"),
            ContentType="application/json",
        )
        return key

    def load(self, model_name: str, version: str) -> Baseline:
        """Load a baseline by model name and version."""

        if self._client is None:  # pragma: no cover - requires AWS at runtime
            raise RuntimeError("BaselineStore has no S3 client configured")
        obj = self._client.get_object(  # type: ignore[attr-defined]
            Bucket=self.bucket, Key=self._key(model_name, version)
        )
        return Baseline.from_json(obj["Body"].read().decode("utf-8"))
