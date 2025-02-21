#!/bin/bash

echo "🚀 Starting LocalStack..."
localstack start -d

# Wait for LocalStack to be ready
echo "⏳ Waiting for LocalStack to be ready..."
sleep 5  # Give it a few seconds to start

# Set LocalStack endpoint
ENDPOINT_URL="http://localhost:4566"

# Create the S3 bucket
BUCKET_NAME="babtestbucket"
echo "🪣 Creating S3 bucket: $BUCKET_NAME"
aws --endpoint-url=$ENDPOINT_URL s3 mb s3://$BUCKET_NAME

echo "✅ LocalStack is ready!"
