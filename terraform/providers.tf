provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "model-monitoring-platform"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
