terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.60.0"
    }
  }
}

provider "aws" {
  region  = "us-east-1"
}

# ✅ Define S3 Bucket
resource "aws_s3_bucket" "clicksend_canary_data" {
  bucket = data.aws_ssm_parameter.s3_bucket.value
}

# ✅ Retrieve Secrets from AWS SSM Parameter Store
data "aws_ssm_parameter" "clicksend_username" {
  name            = "/clicksend/username"
  with_decryption = true
}

data "aws_ssm_parameter" "clicksend_api_key" {
  name            = "/clicksend/api_key"
  with_decryption = true
}

data "aws_ssm_parameter" "s3_bucket" {
  name            = "/s3/bucket"
}

# ✅ IAM Role for Lambda Execution
resource "aws_iam_role" "lambda_role" {
  name = "clicksend-canary-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action = "sts:AssumeRole"
    }]
  })
}

# ✅ IAM Policy for Lambda (S3, CloudWatch, ECR Access)
resource "aws_iam_policy" "lambda_policy" {
  name = "clicksend-canary-lambda-policy"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
     {
        Effect = "Allow",
        Action = ["s3:PutObject", "s3:GetObject", "s3:ListBucket"],
        Resource = "${aws_s3_bucket.clicksend_canary_data.arn}/*"
      },
      {
        Effect = "Allow",
        Action = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow",
        Action = ["ssm:GetParameter"],
        Resource = [
          "arn:aws:ssm:us-east-1:*:parameter/clicksend/username",
          "arn:aws:ssm:us-east-1:*:parameter/clicksend/api_key",
          "arn:aws:ssm:us-east-1:*:parameter/s3/bucket"
        ]
      },
      {
        Effect = "Allow",
        Action = [
          "glue:GetTable",
          "glue:GetTables",
          "glue:GetDatabase",
          "glue:GetDatabases",
          "glue:BatchGetPartition",
          "glue:GetPartition",
          "glue:CreateTable",
          "glue:UpdateTable",
          "glue:DeleteTable"
        ],
        Resource = [
          "arn:aws:glue:us-east-1:${var.account_id}:catalog",
          "arn:aws:glue:us-east-1:${var.account_id}:database/clicksend_canary",
          "arn:aws:glue:us-east-1:${var.account_id}:table/clicksend_canary/sms_logs"
        ]
      },
      {
        Effect = "Allow",
        Action = [
          "athena:StartQueryExecution",
          "athena:GetQueryExecution",
          "athena:GetQueryResults"
        ],
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = [
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:BatchCheckLayerAvailability",
          "ecr:DescribeRepositories",
          "ecr:ListImages",
          "ecr:GetRepositoryPolicy"
        ],
        Resource = aws_ecr_repository.clicksend_canary.arn  # ✅ Fixed Terraform reference
      },
      {
        Effect = "Allow",
        Action = "ecr:GetAuthorizationToken",
        Resource = "*"
      }
    ]
  })
}

# ✅ Attach IAM Policy to IAM Role
resource "aws_iam_role_policy_attachment" "lambda_policy_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_policy.arn
}

# ✅ Lambda Function Definition
resource "aws_lambda_function" "clicksend_canary" {
  function_name = "ClickSendCanary"
  role          = aws_iam_role.lambda_role.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.clicksend_canary.repository_url}:latest"

  timeout = 60

  environment {
    variables = {
      CLICKSEND_USERNAME = data.aws_ssm_parameter.clicksend_username.value
      CLICKSEND_API_KEY  = data.aws_ssm_parameter.clicksend_api_key.value
      S3_BUCKET         = data.aws_ssm_parameter.s3_bucket.value
      S3_ENDPOINT       = "https://s3.amazonaws.com"
    }
  }
}

# ✅ CloudWatch EventBridge Trigger for Lambda
resource "aws_cloudwatch_event_rule" "every_10_minutes" {
  name                = "clicksend-canary-schedule"
  schedule_expression = "rate(10 minutes)"
}

resource "aws_cloudwatch_event_target" "trigger_lambda" {
  rule      = aws_cloudwatch_event_rule.every_10_minutes.name
  target_id = "lambda"
  arn       = aws_lambda_function.clicksend_canary.arn
}

resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.clicksend_canary.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.every_10_minutes.arn
}

# ✅ ECR Repository for Lambda Container
resource "aws_ecr_repository" "clicksend_canary" {
  name = "clicksend-canary"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }
}

# ✅ Attach ECR Policy to Allow Lambda Access
resource "aws_ecr_repository_policy" "clicksend_canary_ecr_policy" {
  repository = aws_ecr_repository.clicksend_canary.name

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        },
        Action = [
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:BatchCheckLayerAvailability"
        ]
      }
    ]
  })
}
