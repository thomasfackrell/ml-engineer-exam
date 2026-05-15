# This configuration uses local state to bootstrap the remote backend
provider "aws" {
  region = "us-east-1"
}

# 1. S3 Bucket to store the Terraform state files
resource "aws_s3_bucket" "terraform_state" {
  # Use the account ID to ensure the bucket name is globally unique
  bucket = "ml-engineer-exam-tf-state-${data.aws_caller_identity.current.account_id}"
  
  # Prevent accidental deletion of this bucket via Terraform
  lifecycle {
    prevent_destroy = true
  }
}

# Enable versioning so you can see the full revision history of your state files
resource "aws_s3_bucket_versioning" "enabled" {
  bucket = aws_s3_bucket.terraform_state.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Enable server-side encryption by default
resource "aws_s3_bucket_server_side_encryption_configuration" "default" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# 2. DynamoDB Table for state locking and consistency
resource "aws_dynamodb_table" "terraform_locks" {
  name         = "ml-engineer-exam-tflock"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }
}

# Data source to get the current AWS Account ID
data "aws_caller_identity" "current" {}

# Outputs to use in the main app/backend.tf configuration
output "state_bucket_name" {
  value       = aws_s3_bucket.terraform_state.id
  description = "The name of the S3 bucket for the remote state"
}

output "dynamodb_table_name" {
  value       = aws_dynamodb_table.terraform_locks.name
  description = "The name of the DynamoDB table for state locking"
}