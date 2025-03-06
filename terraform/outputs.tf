output "lambda_function_arn" {
  description = "ARN of the deployed Lambda function"
  value       = aws_lambda_function.clicksend_canary.arn
}

output "s3_bucket_name" {
  description = "S3 bucket for storing SMS data"
  sensitive   = true
  value       = aws_s3_bucket.clicksend_canary_data.bucket
}

output "lambda_function_name" {
  value = aws_lambda_function.athena_failure_detection_lambda.function_name
}

output "ses_identity_arn" {
  value = aws_ses_email_identity.alerts.arn   # ADDED: Output for SES identity ARN
}