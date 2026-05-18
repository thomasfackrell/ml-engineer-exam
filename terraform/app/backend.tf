terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  backend "s3" {
    # Bucket name applied dynamically in CI OpenTofu CLI call
    key            = "app/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "ml-engineer-exam-tflock"
    encrypt        = true
  }
}

provider "aws" {
  region = "us-east-1"
}