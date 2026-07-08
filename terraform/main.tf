locals {
  name = "${var.name_prefix}-${var.environment}"
}

# ECR repository for the monitoring service container image.
resource "aws_ecr_repository" "app" {
  name                 = local.name
  image_tag_mutability = var.ecr_image_mutability

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }
}

resource "aws_ecr_lifecycle_policy" "app" {
  repository = aws_ecr_repository.app.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Expire untagged images after 14 days"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 14
        }
        action = { type = "expire" }
      }
    ]
  })
}

# S3 storage for reference datasets / baselines, plus the alert topic.
module "monitoring_storage" {
  source = "./modules/monitoring-storage"

  name               = local.name
  force_destroy      = var.baseline_bucket_force_destroy
  enable_alert_topic = var.enable_alert_topic
  alert_email        = var.alert_email
}
