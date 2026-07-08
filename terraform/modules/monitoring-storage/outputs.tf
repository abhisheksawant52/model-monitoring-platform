output "bucket_name" {
  description = "Name of the baselines S3 bucket."
  value       = aws_s3_bucket.baselines.id
}

output "bucket_arn" {
  description = "ARN of the baselines S3 bucket."
  value       = aws_s3_bucket.baselines.arn
}

output "alert_topic_arn" {
  description = "ARN of the SNS alert topic (empty when disabled)."
  value       = var.enable_alert_topic ? aws_sns_topic.alerts[0].arn : ""
}
