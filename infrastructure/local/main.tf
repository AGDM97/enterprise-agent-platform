terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region     = "us-east-1"
  access_key = "test"
  secret_key = "test"

  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  s3_use_path_style           = true

  endpoints {
    s3       = "http://localstack:4566"
    dynamodb = "http://localstack:4566"
    iam      = "http://localstack:4566"
    sts      = "http://localstack:4566"
  }
}

locals {
  project_name = "enterprise-agent-platform"

  common_tags = {
    Project     = local.project_name
    Environment = "local"
    ManagedBy   = "terraform"
  }
}

resource "aws_s3_bucket" "documents" {
  bucket = "enterprise-agent-documents"

  tags = local.common_tags
}

resource "aws_dynamodb_table" "approvals" {
  name         = "enterprise-agent-approvals"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "approval_id"

  attribute {
    name = "approval_id"
    type = "S"
  }

  tags = local.common_tags
}

resource "aws_iam_role" "agent_execution" {
  name = "enterprise-agent-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Effect = "Allow"

        Principal = {
          Service = "lambda.amazonaws.com"
        }

        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy" "agent_permissions" {
  name = "enterprise-agent-permissions"
  role = aws_iam_role.agent_execution.id

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Sid    = "ReadKnowledgeBaseDocuments"
        Effect = "Allow"

        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]

        Resource = [
          aws_s3_bucket.documents.arn,
          "${aws_s3_bucket.documents.arn}/*"
        ]
      },
      {
        Sid    = "ManageHumanApprovals"
        Effect = "Allow"

        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem"
        ]

        Resource = aws_dynamodb_table.approvals.arn
      }
    ]
  })
}

output "documents_bucket" {
  value = aws_s3_bucket.documents.bucket
}

output "approvals_table" {
  value = aws_dynamodb_table.approvals.name
}

output "agent_execution_role_arn" {
  value = aws_iam_role.agent_execution.arn
}