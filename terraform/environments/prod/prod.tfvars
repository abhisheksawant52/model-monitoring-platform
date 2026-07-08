aws_region                    = "us-east-1"
environment                   = "prod"
name_prefix                   = "model-monitoring"
ecr_image_mutability          = "IMMUTABLE"
baseline_bucket_force_destroy = false
enable_alert_topic            = true
alert_email                   = "ml-oncall@example.com"
