FROM public.ecr.aws/lambda/python:3.12

# Install required Python libraries
RUN pip install --no-cache-dir pandas pyarrow boto3 requests

# Copy all source code
COPY main.py /var/task/
COPY src/ /var/task/src/

# ✅ Set the Python path to include /var/task/src
ENV PYTHONPATH="/var/task/src:/var/task"

# Set the Lambda function handler
CMD ["main.lambda_handler"]
