# S3 bucket that stores reference datasets / baseline profiles.
resource "aws_s3_bucket" "baselines" {
  bucket        = "${var.name}-baselines"
  force_destroy = var.force_destroy
}

resource "aws_s3_bucket_versioning" "baselines" {
  bucket = aws_s3_bucket.baselines.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "baselines" {
  bucket = aws_s3_bucket.baselines.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "baselines" {
  bucket = aws_s3_bucket.baselines.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# SNS topic used by the alerting subsystem.
resource "aws_sns_topic" "alerts" {
  count = var.enable_alert_topic ? 1 : 0
  name  = "${var.name}-alerts"
}

resource "aws_sns_topic_subscription" "alert_email" {
  count     = var.enable_alert_topic && var.alert_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alerts[0].arn
  protocol  = "email"
  endpoint  = var.alert_email
}
