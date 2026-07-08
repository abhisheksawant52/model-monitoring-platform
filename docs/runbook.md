# Operations Runbook

Operational guidance for running the model-monitoring-platform service.

## Health and readiness

- `GET /health` — liveness. Returns `200` while the process is serving.
- `GET /ready` — readiness. Kubernetes routes traffic only when this is `200`.
- `GET /metrics` — Prometheus exposition endpoint (port `8000`).

## Common alerts

### Data drift (high PSI / KS)

- **Symptom:** `model_monitoring_drift_score` exceeds `MM_PSI_ALERT_THRESHOLD`
  (default `0.25`) for a feature.
- **Action:** inspect the offending feature's live vs. baseline distribution.
  Confirm whether an upstream data-source change is responsible. If the shift
  is expected, refresh the baseline (see below). If not, consider retraining.

### Concept drift (rising error rate)

- **Symptom:** the concept-drift detector reports an error ratio above the
  configured tolerance.
- **Action:** verify that ground-truth labels are arriving and are correct.
  Escalate to the model owner for retraining if the degradation persists.

### Performance degradation

- **Symptom:** rolling accuracy below `MM_MIN_ACCURACY` or p95 latency above
  `MM_MAX_LATENCY_MS_P95`.
- **Action:** check dependency latency and recent deployments; roll back the
  model version if a regression correlates with a release.

## Refreshing a baseline

1. Recompute the reference profile from a trusted, recent dataset.
2. Persist it via the `BaselineStore` (writes to the S3 baselines bucket).
3. Point the service at the new version and confirm drift scores normalise.

## Deploying

- Container image is published to ECR / GHCR and rolled out via the Helm chart
  in `helm/model-monitoring`.
- Infrastructure (ECR, S3, SNS) is managed by Terraform under `terraform/`.

## Escalation

Page the ML platform on-call via the SNS alert topic. Include the affected
model name, feature, and the drift/performance metric values from Grafana.
