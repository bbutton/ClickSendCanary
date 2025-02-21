#!/bin/bash

echo "🛑 Stopping LocalStack..."
localstack stop

echo "🧹 Cleaning up LocalStack Docker containers..."
docker rm -f localstack_main 2>/dev/null

echo "✅ LocalStack stopped and cleaned up."
