#!/bin/bash

docker run --rm -v "$PWD":/var/task:ro,delegated \
    -e CLICKSEND_USERNAME='BABUTTON' \
    -e CLICKSEND_API_KEY=''31E2919C-08AB-6979-E859-9F5438C76746 \
    -e S3_BUCKET='clicksend-canary-data' \
    public.ecr.aws/lambda/python:3.12 \
    python3 -m src.main
