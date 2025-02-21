# src/storage.py

import pandas as pd
import boto3
import io
import os
from datetime import datetime

def convert_to_parquet(messages):
    """
    Converts a list of message dictionaries into a Parquet file stored in memory.
    Returns the Parquet data as bytes.
    """
    df = pd.DataFrame(messages)
    parquet_buffer = io.BytesIO()
    df.to_parquet(parquet_buffer, index=False)
    return parquet_buffer.getvalue()

S3_BUCKET = os.getenv("S3_BUCKET", "babtestbucket")  # Default to LocalStack bucket
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://localhost:4566")  # Default to LocalStack

def store_messages(messages):
    if not messages:
        return

    s3_client = boto3.client("s3", endpoint_url=S3_ENDPOINT)  # Use LocalStack
    parquet_data = convert_to_parquet(messages)

    timestamp = datetime.strptime(messages[0]["timestamp"], "%Y-%m-%d %H:%M:%S")
    s3_key = f"sms-logs/year={timestamp.year}/month={timestamp.month:02}/day={timestamp.day:02}/messages.parquet"

    response = s3_client.put_object(Bucket=S3_BUCKET, Key=s3_key, Body=parquet_data)
