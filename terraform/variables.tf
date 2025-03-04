variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "lambda_function_name" {
  description = "Name of the Lambda function"
  type        = string
  default     = "ClickSendCanary"
}

variable "account_id" {
  description = "Account id to use for all this stuff"
  type        = number
  default     = "095750864911"
}