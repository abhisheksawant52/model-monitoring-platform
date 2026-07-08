"""Application configuration via pydantic-settings.

Settings are read from environment variables (optionally prefixed with
``MM_``) and from a local ``.env`` file. See ``.env.example`` for the full
list of supported variables.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the monitoring service."""

    model_config = SettingsConfigDict(
        env_prefix="MM_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Service ---------------------------------------------------------
    app_name: str = Field(default="model-monitoring-platform")
    environment: str = Field(default="development")
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    log_level: str = Field(default="INFO")

    # --- Drift detection thresholds -------------------------------------
    psi_warn_threshold: float = Field(
        default=0.1,
        description="Population Stability Index above which drift is a warning.",
    )
    psi_alert_threshold: float = Field(
        default=0.25,
        description="Population Stability Index above which drift is critical.",
    )
    ks_pvalue_threshold: float = Field(
        default=0.05,
        description="p-value below which the KS test flags distribution drift.",
    )

    # --- Performance thresholds -----------------------------------------
    min_accuracy: float = Field(default=0.80)
    max_latency_ms_p95: float = Field(default=250.0)
    rolling_window: int = Field(default=1000)

    # --- Baseline storage (S3) ------------------------------------------
    baseline_bucket: str = Field(default="model-monitoring-baselines")
    baseline_prefix: str = Field(default="baselines/")
    aws_region: str = Field(default="us-east-1")

    # --- Alerting --------------------------------------------------------
    alert_sns_topic_arn: str | None = Field(default=None)
    alert_webhook_url: str | None = Field(default=None)


@lru_cache
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance."""

    return Settings()
