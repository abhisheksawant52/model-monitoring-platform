variable "aws_region" {
  description = "AWS region for all resources."
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment name (e.g. dev, prod)."
  type        = string
  default     = "dev"
}

variable "name_prefix" {
  description = "Prefix applied to resource names for uniqueness."
  type        = string
  default     = "model-monitoring"
}

variable "ecr_image_mutability" {
  description = "ECR image tag mutability (MUTABLE or IMMUTABLE)."
  type        = string
  default     = "IMMUTABLE"
}

variable "baseline_bucket_force_destroy" {
  description = "Allow Terraform to destroy the baseline bucket even if non-empty."
  type        = bool
  default     = false
}

variable "enable_alert_topic" {
  description = "Whether to create the SNS topic used for monitoring alerts."
  type        = bool
  default     = true
}

variable "alert_email" {
  description = "Optional email address subscribed to the alert SNS topic."
  type        = string
  default     = ""
}
