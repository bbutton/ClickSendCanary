import pyarrow.parquet as pq
import pyarrow as pa
import boto3
import os
import io
from datetime import datetime
from src.time_utils import convert_from_epoch

def get_s3_client():
    s3_endpoint = os.getenv("S3_ENDPOINT")
    s3_bucket = os.getenv("S3_BUCKET")

    if not s3_endpoint or not s3_bucket:
        raise EnvironmentError("Missing required environment variables: S3_ENDPOINT or S3_BUCKET.")

    return boto3.client("s3", endpoint_url=s3_endpoint), s3_bucket

def convert_to_parquet(messages):
    if not messages:
        raise ValueError("No messages to convert to Parquet.")

    table = pa.Table.from_pydict({key: [msg[key] for msg in messages] for key in messages[0]})

    buffer = io.BytesIO()
    pq.write_table(table, buffer)

    return buffer.getvalue()

def store_messages(messages):
    print(f"Attempting to store {len(messages)} messages")

    if not messages:
        return

    s3_client, s3_bucket = get_s3_client()

    parquet_data = convert_to_parquet(messages)

    # Determine the S3 key path based on the first message's timestamp
    timestamp = convert_from_epoch(int(messages[0]["date"]))
    s3_name_timestamp = generate_s3_key(timestamp)
    s3_key = f"sms-logs/{s3_name_timestamp}"

    response = s3_client.put_object(Bucket=s3_bucket, Key=s3_key, Body=parquet_data, ContentType="application/parquet")

    print(f"Uploaded {len(messages)} messages to {s3_key}")

def generate_s3_key(timestamp: datetime) -> str:
    return (
        f"year={timestamp.strftime('%Y')}/"
        f"month={timestamp.strftime('%m')}/"
        f"day={timestamp.strftime('%d')}/"
        f"messages-{timestamp.strftime('%H-%M-%S')}.parquet"
    )
