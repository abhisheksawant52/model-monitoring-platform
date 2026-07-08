# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-07-08

### Added

- FastAPI service with `/health`, `/ready`, `/metrics`, and
  `/v1/drift/check` endpoints.
- Data-drift detectors (Population Stability Index, Kolmogorov–Smirnov) and a
  concept-drift detector based on rolling error-rate degradation.
- Rolling performance tracker (accuracy, precision, recall, latency
  percentiles).
- Threshold-rule alerting with pluggable channels (log, AWS SNS).
- Baseline management with S3-backed storage.
- Prometheus-style metrics exposition.
- Helm chart (`helm/model-monitoring`) with deployment, service, ingress,
  HPA, service account, and ServiceMonitor templates.
- Terraform for ECR, S3 baseline storage, and an SNS alert topic, with
  `dev`/`prod` environments and a `monitoring-storage` module.
- Multi-stage, non-root Dockerfile with a `/health` healthcheck.
- CI pipeline, pre-commit hooks, and open-source project files.
