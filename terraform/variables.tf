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

variable "ses_source_email" {
  description = "Source email for SES alerts"
  type        = string
  default     = "brian.button@copeland.com"
}

variable "alert_recipients" {
  description = "Comma-separated list of email recipients for alerts"
  type        = string
  default     = "bbutton@gmail.com, brian.button@copeland.com, christian.barnett@copeland.com, scott.fritz@copeland.com"
}