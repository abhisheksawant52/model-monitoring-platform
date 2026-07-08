"""Prometheus-style metrics exposition.

A tiny, dependency-free registry that renders metrics in the Prometheus text
exposition format. This keeps the package importable without pulling in the
full ``prometheus_client`` while remaining scrape-compatible. Swap for
``prometheus_client`` in production if richer semantics are required.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field

Labels = tuple[tuple[str, str], ...]


def _format_labels(labels: Labels) -> str:
    if not labels:
        return ""
    inner = ",".join(f'{k}="{v}"' for k, v in labels)
    return "{" + inner + "}"


@dataclass
class MetricFamily:
    """A named metric with help text and label-keyed samples."""

    name: str
    help_text: str
    metric_type: str = "gauge"
    samples: dict[Labels, float] = field(default_factory=dict)


class MetricsRegistry:
    """Thread-safe registry of gauges and counters."""

    def __init__(self) -> None:
        self._families: dict[str, MetricFamily] = {}
        self._lock = threading.Lock()

    def _family(self, name: str, help_text: str, metric_type: str) -> MetricFamily:
        fam = self._families.get(name)
        if fam is None:
            fam = MetricFamily(name=name, help_text=help_text, metric_type=metric_type)
            self._families[name] = fam
        return fam

    def set_gauge(
        self, name: str, value: float, help_text: str = "", **labels: str
    ) -> None:
        """Set a gauge sample to ``value``."""

        with self._lock:
            fam = self._family(name, help_text, "gauge")
            fam.samples[tuple(sorted(labels.items()))] = float(value)

    def inc_counter(
        self, name: str, amount: float = 1.0, help_text: str = "", **labels: str
    ) -> None:
        """Increment a counter sample by ``amount``."""

        with self._lock:
            fam = self._family(name, help_text, "counter")
            key = tuple(sorted(labels.items()))
            fam.samples[key] = fam.samples.get(key, 0.0) + float(amount)

    def render(self) -> str:
        """Render all metrics in the Prometheus text exposition format."""

        lines: list[str] = []
        with self._lock:
            for fam in self._families.values():
                if fam.help_text:
                    lines.append(f"# HELP {fam.name} {fam.help_text}")
                lines.append(f"# TYPE {fam.name} {fam.metric_type}")
                for labels, value in fam.samples.items():
                    lines.append(f"{fam.name}{_format_labels(labels)} {value}")
        return "\n".join(lines) + "\n"


# Module-level default registry used by the API layer.
REGISTRY = MetricsRegistry()

CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"
