import boto3
import json

def lambda_handler(event, context):
    athena_client = boto3.client("athena")

    # ✅ Replacing CALL with the actual SQL query
    failure_query = """
¬        SELECT 1
    """

    response = athena_client.start_query_execution(
        QueryString=failure_query,
        WorkGroup="clicksend-canary-workgroup",
        ResultConfiguration={'OutputLocation': "s3://clicksend-canary-data/athena-query-results/"}
    )

    return {"QueryExecutionId": response["QueryExecutionId"]}
