# ✅ Glue Database & Table
resource "aws_glue_catalog_database" "clicksend_canary" {
  name = "clicksend_canary"
}

resource "aws_glue_catalog_table" "sms_logs" {
  name          = "sms_logs"
  database_name = aws_glue_catalog_database.clicksend_canary.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    "classification"       = "parquet"
    "parquet.compression"  = "SNAPPY"
  }

  storage_descriptor {
    location      = "s3://clicksend-canary-data/sms-logs/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }

    columns {
      name = "direction"
      type = "string"
    }
    columns {
      name = "sent_date"
      type = "bigint"
    }
    columns {
      name = "`to`"
      type = "string"
    }
    columns {
      name = "body"
      type = "string"
    }
    columns {
      name = "`from`"
      type = "string"
    }
    columns {
      name = "status_code"
      type = "string"
    }
    columns {
      name = "message_id"
      type = "string"
    }
    columns {
      name = "message_parts"
      type = "int"
    }
    columns {
      name = "message_price"
      type = "string"
    }
    columns {
      name = "from_email"
      type = "string"
    }
  }

  partition_keys {
    name = "year"
    type = "string"
  }
  partition_keys {
    name = "month"
    type = "string"
  }
  partition_keys {
    name = "day"
    type = "string"
  }
}

# ✅ Athena Workgroup
resource "aws_athena_workgroup" "clicksend_canary_workgroup" {
  name = "clicksend-canary-workgroup"

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true
    result_configuration {
      output_location = "s3://clicksend-canary-data/athena-query-results/"
    }
  }
}

# ✅ Failure Detection Lambda
resource "aws_lambda_function" "athena_failure_detection_lambda" {
  function_name = "AthenaFailureDetectionLambda"
  role          = aws_iam_role.athena_failure_lambda_role.arn
  runtime       = "python3.12"
  handler       = "athena_failure.lambda_handler"

  s3_bucket = aws_s3_bucket.clicksend_canary_data.id
  s3_key    = "athena_failure.zip"

  timeout = 60

  environment {
    variables = {
      ATHENA_WORKGROUP = aws_athena_workgroup.clicksend_canary_workgroup.name
      ATHENA_QUERY     = aws_athena_named_query.failure_detection.id
    }
  }
}

# ✅ Athena Named Query for Failure Detection
resource "aws_athena_named_query" "failure_detection" {
  name      = "clicksend_failure_detection"
  database  = aws_glue_catalog_database.clicksend_canary.name
  workgroup = aws_athena_workgroup.clicksend_canary_workgroup.name
  query     = <<EOF
WITH failure_analysis AS (
    SELECT
        date_trunc('minute', from_unixtime(sent_date)) AS time_window,
        COUNT(*) AS total_messages,
        SUM(CASE WHEN status_code NOT IN ('200', '201') THEN 1 ELSE 0 END) AS failed_messages
    FROM clicksend_canary.sms_logs
    WHERE from_unixtime(sent_date) >= now() - interval '60' minute
    AND direction = 'out'
    GROUP BY date_trunc('minute', from_unixtime(sent_date))
),
sliding_window AS (
    SELECT
        fa1.time_window,
        SUM(fa2.total_messages) AS total_messages,
        SUM(fa2.failed_messages) AS failed_messages
    FROM failure_analysis fa1
    JOIN failure_analysis fa2
    ON fa2.time_window BETWEEN fa1.time_window - interval '30' minute AND fa1.time_window
    GROUP BY fa1.time_window
)
SELECT
    time_window,
    total_messages,
    failed_messages,
    (failed_messages * 100.0) / NULLIF(total_messages, 0) AS failure_rate,
    CASE
        WHEN (failed_messages * 100.0) / NULLIF(total_messages, 0) >= 25 THEN 'CRITICAL'
        WHEN (failed_messages * 100.0) / NULLIF(total_messages, 0) >= 3 THEN 'WARNING'
        ELSE 'OK'
    END AS alert_level
FROM sliding_window
ORDER BY time_window DESC;
EOF
}

# ✅ CloudWatch Event to Run Failure Detection Lambda
resource "aws_cloudwatch_event_rule" "athena_failure_schedule" {
  name                = "athena-failure-detection-schedule"
  schedule_expression = "rate(10 minutes)"
}

resource "aws_cloudwatch_event_target" "athena_lambda_target" {
  rule = aws_cloudwatch_event_rule.athena_failure_schedule.name
  arn  = aws_lambda_function.athena_failure_detection_lambda.arn
}

# ✅ IAM Role for Athena Failure Detection Lambda
resource "aws_iam_role" "athena_failure_lambda_role" {
  name = "athena-failure-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action = "sts:AssumeRole"
    }]
  })
}

# ✅ IAM Policy for Athena Failure Detection Lambda
resource "aws_iam_policy" "athena_failure_lambda_policy" {
  name        = "athena-failure-lambda-policy"
  description = "Allows Lambda to query Athena and log results"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow"
        Action   = [
          "athena:StartQueryExecution",
          "athena:GetQueryExecution",
          "athena:GetQueryResults"
        ]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = "arn:aws:s3:::clicksend-canary-data/athena-query-results/*"
      },
      {
        Effect   = "Allow"
        Action   = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# ✅ Attach IAM Policy to Athena Failure Detection Lambda Role
resource "aws_iam_role_policy_attachment" "athena_failure_lambda_policy_attachment" {
  role       = aws_iam_role.athena_failure_lambda_role.name
  policy_arn = aws_iam_policy.athena_failure_lambda_policy.arn
}

#### All scheduler stuff below here ####

# ✅ Schedule MSCK REPAIR TABLE at Midnight UTC
resource "aws_scheduler_schedule" "athena_repair_schedule_midnight" {
  name       = "athena-msck-repair-midnight"
  flexible_time_window {
    mode = "OFF"
  }
  schedule_expression = "cron(0 0 * * ? *)"  # ✅ Runs at 00:00 UTC
  target {
    arn      = "arn:aws:scheduler:::aws-sdk:athena:startQueryExecution"
    role_arn = aws_iam_role.athena_scheduler_role.arn
    input = jsonencode({
      QueryString          = aws_athena_named_query.msck_repair.query
      QueryExecutionContext = { Database = aws_glue_catalog_database.clicksend_canary.name }
      ResultConfiguration  = { OutputLocation = "s3://clicksend-canary-data/athena-query-results/" }
    })
  }
}

# ✅ Schedule a Second Repair 15 Minutes Later (Backup)
resource "aws_scheduler_schedule" "athena_repair_schedule_backup" {
  name       = "athena-msck-repair-backup"
  flexible_time_window {
    mode = "OFF"
  }
  schedule_expression = "cron(15 0 * * ? *)"  # ✅ Runs at 00:15 UTC
  target {
    arn      = "arn:aws:scheduler:::aws-sdk:athena:startQueryExecution"
    role_arn = aws_iam_role.athena_scheduler_role.arn
    input = jsonencode({
      QueryString          = aws_athena_named_query.msck_repair.query
      QueryExecutionContext = { Database = aws_glue_catalog_database.clicksend_canary.name }
      ResultConfiguration  = { OutputLocation = "s3://clicksend-canary-data/athena-query-results/" }
    })
  }
}

# ✅ Named Query for MSCK REPAIR TABLE
resource "aws_athena_named_query" "msck_repair" {
  name        = "daily_msck_repair"
  description = "Runs MSCK REPAIR TABLE for partition updates at 00:00 and 00:15 UTC daily."
  database    = aws_glue_catalog_database.clicksend_canary.name
  query       = "MSCK REPAIR TABLE clicksend_canary.sms_logs;"
}

# ✅ IAM Role for EventBridge Scheduler to Execute Athena Queries
resource "aws_iam_role" "athena_scheduler_role" {
  name = "athena-scheduler-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = { Service = "scheduler.amazonaws.com" }
      Action = "sts:AssumeRole"
    }]
  })
}

# ✅ IAM Policy for Athena Scheduler Role
resource "aws_iam_policy" "athena_scheduler_policy" {
  name        = "athena-scheduler-policy"
  description = "Allows EventBridge Scheduler to run Athena queries"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = [
          "athena:StartQueryExecution"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ],
        Resource = "arn:aws:s3:::clicksend-canary-data/athena-query-results/*"
      },
      {
        Effect   = "Allow"
        Action   = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# ✅ Attach IAM Policy to Athena Scheduler Role
resource "aws_iam_role_policy_attachment" "athena_scheduler_role_attach" {
  role       = aws_iam_role.athena_scheduler_role.name
  policy_arn = aws_iam_policy.athena_scheduler_policy.arn
}