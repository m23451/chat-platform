terraform {
    required_version =">= 1.10"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.region

  # tags all resources in this project, good for cleanup
  default_tags {
    tags = {
      project    = "chat-demo"
      managed-by = "terraform"
    }
  }
}