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
      name                  = "ParquetSerDe"
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
      QueryExecutionContext = { Database = "clicksend_canary" }
      ResultConfiguration  = { OutputLocation = "s3://your-athena-query-results/" }
    })
  }
}

# ✅ Schedule a Second Repair 15 Minutes Later (Just in Case)
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
      QueryExecutionContext = { Database = "clicksend_canary" }
      ResultConfiguration  = { OutputLocation = "s3://your-athena-query-results/" }
    })
  }
}

resource "aws_athena_named_query" "msck_repair" {
  name        = "daily_msck_repair"
  description = "Runs MSCK REPAIR TABLE for partition updates at 00:00 and 00:15 UTC daily."
  database    = aws_glue_catalog_database.clicksend_canary.name
  query       = "MSCK REPAIR TABLE clicksend_canary.sms_logs;"
}

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

resource "aws_iam_policy" "athena_scheduler_policy" {
  name        = "athena-scheduler-policy"
  description = "Allows AWS Scheduler to run Athena queries"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["athena:StartQueryExecution"]
      Resource = "*"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "athena_scheduler_attachment" {
  role       = aws_iam_role.athena_scheduler_role.name
  policy_arn = aws_iam_policy.athena_scheduler_policy.arn
}