output "ecr_repository_url" {
  description = "URL of the ECR repository for the service image."
  value       = aws_ecr_repository.app.repository_url
}

output "baseline_bucket_name" {
  description = "Name of the S3 bucket storing model baselines."
  value       = module.monitoring_storage.bucket_name
}

output "baseline_bucket_arn" {
  description = "ARN of the S3 bucket storing model baselines."
  value       = module.monitoring_storage.bucket_arn
}

output "alert_topic_arn" {
  description = "ARN of the SNS alert topic (empty when disabled)."
  value       = module.monitoring_storage.alert_topic_arn
}
