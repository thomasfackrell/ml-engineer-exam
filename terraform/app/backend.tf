terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  backend "s3" {
    # This matches the bucket name created by the bootstrap run
    bucket         = "ml-engineer-exam-tf-state-${data.aws_caller_identity.current.account_id}"
    key            = "app/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "ml-engineer-exam-tflock"
    encrypt        = true
  }
}

provider "aws" {
  region = "us-east-1"
}