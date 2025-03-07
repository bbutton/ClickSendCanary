# Lambda for Athena MSCK REPAIR
resource "aws_lambda_function" "athena_repair_lambda" {
  function_name = "AthenaRepairLambda"
  description   = "Executes MSCK REPAIR TABLE on schedule for Athena partitions"
  role          = aws_iam_role.athena_repair_lambda_role.arn
  runtime       = "python3.12"
  handler       = "athena_repair_lambda.lambda_handler"
  timeout       = 60

   # Use s3_bucket and s3_key instead of filename
  s3_bucket = "clicksend-canary-data"
  s3_key    = "athena_repair_lambda.zip"

  environment {
    variables = {
      ATHENA_DATABASE  = aws_glue_catalog_database.clicksend_canary.name
      ATHENA_TABLE     = "sms_logs"
      ATHENA_WORKGROUP = aws_athena_workgroup.clicksend_canary_workgroup.name
      S3_OUTPUT_BUCKET = aws_s3_bucket.clicksend_canary_data.id
      S3_OUTPUT_PREFIX = "athena-query-results/"
    }
  }
}

# IAM Role for the Lambda
resource "aws_iam_role" "athena_repair_lambda_role" {
  name = "athena-repair-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

# IAM Policy for the Lambda
resource "aws_iam_policy" "athena_repair_lambda_policy" {
  name        = "athena-repair-lambda-policy"
  description = "Allows Lambda to execute Athena MSCK REPAIR"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "athena:StartQueryExecution",
          "athena:GetQueryExecution",
          "athena:GetQueryResults",
          "athena:GetWorkGroup"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:GetBucketLocation",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${aws_s3_bucket.clicksend_canary_data.id}",
          "arn:aws:s3:::${aws_s3_bucket.clicksend_canary_data.id}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "glue:GetDatabase",
          "glue:GetTable",
          "glue:GetPartition",
          "glue:GetPartitions",
          "glue:BatchCreatePartition",
          "glue:BatchDeletePartition"
        ]
        Resource = [
          "arn:aws:glue:${var.aws_region}:${data.aws_caller_identity.current.account_id}:catalog",
          "arn:aws:glue:${var.aws_region}:${data.aws_caller_identity.current.account_id}:database/${aws_glue_catalog_database.clicksend_canary.name}",
          "arn:aws:glue:${var.aws_region}:${data.aws_caller_identity.current.account_id}:table/${aws_glue_catalog_database.clicksend_canary.name}/sms_logs"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# Attach policy to role
resource "aws_iam_role_policy_attachment" "athena_repair_policy_attachment" {
  role       = aws_iam_role.athena_repair_lambda_role.name
  policy_arn = aws_iam_policy.athena_repair_lambda_policy.arn
}

# CloudWatch Event Rule for midnight UTC
resource "aws_cloudwatch_event_rule" "athena_repair_midnight" {
  name                = "athena-repair-midnight"
  description         = "Trigger Athena MSCK REPAIR at midnight UTC"
  schedule_expression = "cron(0 0 * * ? *)"
}

# CloudWatch Event Target for midnight rule
resource "aws_cloudwatch_event_target" "athena_repair_midnight_target" {
  rule      = aws_cloudwatch_event_rule.athena_repair_midnight.name
  target_id = "AthenaRepairLambda"
  arn       = aws_lambda_function.athena_repair_lambda.arn
}

# CloudWatch Event Rule for 00:15 UTC (backup)
resource "aws_cloudwatch_event_rule" "athena_repair_backup" {
  name                = "athena-repair-backup"
  description         = "Trigger Athena MSCK REPAIR at 00:15 UTC (backup)"
  schedule_expression = "cron(15 0 * * ? *)"
}

# CloudWatch Event Target for backup rule
resource "aws_cloudwatch_event_target" "athena_repair_backup_target" {
  rule      = aws_cloudwatch_event_rule.athena_repair_backup.name
  target_id = "AthenaRepairLambdaBackup"
  arn       = aws_lambda_function.athena_repair_lambda.arn
}

# Lambda permissions for CloudWatch Events
resource "aws_lambda_permission" "allow_cloudwatch_midnight" {
  statement_id  = "AllowExecutionFromCloudWatchMidnight"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.athena_repair_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.athena_repair_midnight.arn
}

resource "aws_lambda_permission" "allow_cloudwatch_backup" {
  statement_id  = "AllowExecutionFromCloudWatchBackup"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.athena_repair_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.athena_repair_backup.arn
}