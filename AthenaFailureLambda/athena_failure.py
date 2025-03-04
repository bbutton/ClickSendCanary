import boto3
import os

def lambda_handler(event, context):
    athena_client = boto3.client("athena")

    response = athena_client.start_query_execution(
        QueryString="CALL clicksend_canary.failure_detection();",
        WorkGroup=os.environ["ATHENA_WORKGROUP"]
    )

    return {"QueryExecutionId": response["QueryExecutionId"]}
