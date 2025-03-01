resource "aws_glue_catalog_database" "clicksend_canary" {
  name = "clicksend_canary"
}

resource "aws_glue_catalog_table" "sms_logs_json" {
  name          = "sms_logs_json"
  database_name = aws_glue_catalog_database.clicksend_canary.name

  table_type = "EXTERNAL_TABLE"

  parameters = {
    "classification" = "json"
  }

  storage_descriptor {
    location      = "s3://clicksend-canary-data/sms-logs/"
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"

    ser_de_info {
      name                  = "json"
      serialization_library = "org.openx.data.jsonserde.JsonSerDe"
    }

    columns {
      name = "direction"
      type = "string"
    }

    columns {
      name = "`date`"
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
      type = "decimal(10,4)"
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

resource "aws_glue_catalog_table" "sms_logs" {
  name          = "sms_logs"
  database_name = aws_glue_catalog_database.clicksend_canary.name

  table_type = "EXTERNAL_TABLE"

  parameters = {
    "parquet.compression" = "SNAPPY"
  }

  storage_descriptor {
    location      = "s3://clicksend-canary-data/parquet/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    ser_de_info {
      name                  = "parquet"
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }

    columns {
      name = "direction"
      type = "string"
    }

    columns {
      name = "`date`"
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
      type = "decimal(10,4)"
    }

    columns {
      name = "from_email"
      type = "string"
    }
  }
}

resource "aws_athena_workgroup" "clicksend_canary_workgroup" {
  name = "clicksend-canary-workgroup"

  configuration {
    enforce_workgroup_configuration = true

    result_configuration {
      output_location = "s3://clicksend-canary-data/athena-query-results/"
    }
  }
}

