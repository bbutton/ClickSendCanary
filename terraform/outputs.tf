output "lambda_function_arn" {
  description = "ARN of the deployed Lambda function"
  value       = aws_lambda_function.clicksend_canary.arn
}

output "s3_bucket_name" {
  description = "S3 bucket for storing SMS data"
  sensitive = true
  value       = aws_s3_bucket.clicksend_canary_data.bucket
}