terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.60.0"  # ✅ Use a stable version instead of latest
    }
  }
}

provider "aws" {
  region  = "us-east-1"  # ✅ Change to your AWS region
  profile = "terraform-deployer"  # ✅ Ensure you're using a limited IAM user
}

# ✅ Define S3 Bucket using the Parameter Store Value
resource "aws_s3_bucket" "clicksend_canary_data" {
  bucket = data.aws_ssm_parameter.s3_bucket.value
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

# ✅ IAM Policy for Lambda (S3 & CloudWatch Logs Access)
resource "aws_iam_policy" "lambda_policy" {
  name = "clicksend-canary-lambda-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow",
        Action = ["s3:PutObject", "s3:GetObject"],
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
      }
    ]
  })
}

# ✅ Attach IAM Policy to IAM Role
resource "aws_iam_role_policy_attachment" "lambda_policy_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_policy.arn
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

# ✅ Lambda Function Definition (Code Must Be Packaged and Uploaded to S3)
resource "aws_lambda_function" "clicksend_canary" {
  function_name    = "ClickSendCanary"
  role            = aws_iam_role.lambda_role.arn
  handler         = "main.lambda_handler"
  runtime         = "python3.12"

  s3_bucket       = aws_s3_bucket.clicksend_canary_data.id
  s3_key          = "lambda.zip"  # ✅ Upload this file before running Terraform

  timeout         = 60

  environment {
    variables = {
      CLICKSEND_USERNAME = data.aws_ssm_parameter.clicksend_username.value
      CLICKSEND_API_KEY  = data.aws_ssm_parameter.clicksend_api_key.value
      S3_BUCKET         = data.aws_ssm_parameter.s3_bucket.value
    }
  }
}

# ✅ CloudWatch Event to Trigger Lambda Every 10 Minutes
resource "aws_cloudwatch_event_rule" "every_10_minutes" {
  name        = "clicksend-canary-schedule"
  description = "Triggers Lambda every 10 minutes"
  schedule_expression = "rate(10 minutes)"
}

resource "aws_cloudwatch_event_target" "trigger_lambda" {
  rule      = aws_cloudwatch_event_rule.every_10_minutes.name
  target_id = "lambda"
  arn       = aws_lambda_function.clicksend_canary.arn
}

# ✅ Allow CloudWatch to Invoke Lambda
resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.clicksend_canary.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.every_10_minutes.arn
}