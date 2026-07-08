"""Alerting: threshold rules and pluggable notification channels.

The alerting layer separates *what* is wrong (threshold rules evaluated
against drift and performance signals) from *where* the notification goes
(channels). New channels only need to implement :class:`AlertChannel`.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class AlertLevel(str, Enum):
    """Severity of an emitted alert."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass(frozen=True)
class Alert:
    """A single alert to be dispatched to one or more channels."""

    title: str
    message: str
    level: AlertLevel
    labels: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ThresholdRule:
    """A rule that fires when a metric crosses a threshold.

    Attributes:
        name: Human-readable rule name.
        metric: Metric key this rule applies to.
        threshold: Comparison threshold.
        comparison: Either ``"gt"`` (fire when value > threshold) or ``"lt"``
            (fire when value < threshold).
        level: Severity to emit when the rule fires.
    """

    name: str
    metric: str
    threshold: float
    comparison: str = "gt"
    level: AlertLevel = AlertLevel.WARNING

    def evaluate(self, value: float) -> Alert | None:
        """Return an :class:`Alert` if the rule fires, else ``None``."""

        fired = value > self.threshold if self.comparison == "gt" else value < self.threshold
        if not fired:
            return None
        return Alert(
            title=f"{self.name} triggered",
            message=(
                f"metric '{self.metric}' = {value:.4f} "
                f"({self.comparison} {self.threshold})"
            ),
            level=self.level,
            labels={"metric": self.metric, "rule": self.name},
        )


class AlertChannel(ABC):
    """Abstract notification channel."""

    @abstractmethod
    def send(self, alert: Alert) -> None:
        """Deliver ``alert`` to the underlying transport."""


class LogChannel(AlertChannel):
    """Channel that writes alerts to the application log."""

    def send(self, alert: Alert) -> None:
        logger.warning(
            "ALERT [%s] %s: %s",
            alert.level.value,
            alert.title,
            alert.message,
            extra={"extra_fields": {"labels": alert.labels}},
        )


class SNSChannel(AlertChannel):
    """Channel that publishes alerts to an AWS SNS topic.

    The boto3 client is injected so the class stays testable and importable
    without AWS credentials present.
    """

    def __init__(self, topic_arn: str, client: object | None = None) -> None:
        self.topic_arn = topic_arn
        self._client = client

    def send(self, alert: Alert) -> None:
        if self._client is None:  # pragma: no cover - requires AWS at runtime
            logger.info("SNS channel not wired; dropping alert %s", alert.title)
            return
        self._client.publish(  # type: ignore[attr-defined]
            TopicArn=self.topic_arn,
            Subject=alert.title[:100],
            Message=alert.message,
            MessageAttributes={
                "level": {"DataType": "String", "StringValue": alert.level.value}
            },
        )


class AlertManager:
    """Evaluate threshold rules and fan alerts out to channels."""

    def __init__(
        self,
        rules: list[ThresholdRule] | None = None,
        channels: list[AlertChannel] | None = None,
    ) -> None:
        self.rules = rules or []
        self.channels = channels or [LogChannel()]

    def evaluate(self, metrics: dict[str, float]) -> list[Alert]:
        """Evaluate all rules against ``metrics`` and dispatch fired alerts.

        Args:
            metrics: Mapping of metric key to current value.

        Returns:
            The list of alerts that fired (and were dispatched).
        """

        fired: list[Alert] = []
        for rule in self.rules:
            if rule.metric not in metrics:
                continue
            alert = rule.evaluate(metrics[rule.metric])
            if alert is not None:
                fired.append(alert)
                self._dispatch(alert)
        return fired

    def _dispatch(self, alert: Alert) -> None:
        for channel in self.channels:
            try:
                channel.send(alert)
            except Exception:  # noqa: BLE001 - a channel failure must not break monitoring
                logger.exception("Failed to send alert via %s", type(channel).__name__)
