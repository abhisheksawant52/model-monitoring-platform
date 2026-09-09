terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.63"
    }
  }

  # Configure a remote backend per environment. Example (partial config):
  # backend "s3" {
  #   bucket = "my-terraform-state"
  #   key    = "model-monitoring/terraform.tfstate"
  #   region = "us-east-1"
  # }
}
