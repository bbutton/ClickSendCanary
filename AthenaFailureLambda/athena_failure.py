import boto3
import os
import json
import time



ATHENA_WORKGROUP = os.getenv("ATHENA_WORKGROUP")


def lambda_handler(event, context):
    s3_client = boto3.client("s3")
    athena_client = boto3.client("athena")

    failure_query = """
    SELECT
        COUNT(*) AS total_messages,
        SUM(CASE WHEN status_code NOT IN ('200', '201') THEN 1 ELSE 0 END) AS failed_messages,
        (SUM(CASE WHEN status_code NOT IN ('200', '201') THEN 1 ELSE 0 END) * 100.0) / NULLIF(COUNT(*), 0) AS failure_rate,
        CASE
            WHEN (SUM(CASE WHEN status_code NOT IN ('200', '201') THEN 1 ELSE 0 END) * 100.0) / NULLIF(COUNT(*), 0) >= 25 THEN 'CRITICAL'
            WHEN (SUM(CASE WHEN status_code NOT IN ('200', '201') THEN 1 ELSE 0 END) * 100.0) / NULLIF(COUNT(*), 0) >= 3 THEN 'WARNING'
            ELSE 'OK'
        END AS alert_level
    FROM clicksend_canary.sms_logs
    WHERE from_unixtime(sent_date) >= now() - interval '30' minute
    AND direction = 'out';
    """

    import json
    import traceback

    try:
        response = athena_client.start_query_execution(
            QueryString=failure_query,
            WorkGroup=os.environ["ATHENA_WORKGROUP"]
        )

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Query started successfully",
                "QueryExecutionId": response["QueryExecutionId"]
            })
        }

    except Exception as e:
        error_details = traceback.format_exc()  # Captures full error details
        print(f"❌ ERROR: {error_details}")  # Prints entire error log for debugging

        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e), "stack_trace": error_details})  # Returns full trace
        }

    query_execution_id = response["QueryExecutionId"]

    # ✅ Wait for the query to complete
    while True:
        query_status = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
        state = query_status["QueryExecution"]["Status"]["State"]

        if state in ["SUCCEEDED", "FAILED", "CANCELLED"]:
            break
        time.sleep(1)  # Small delay to avoid excessive API calls

    if state != "SUCCEEDED":
        return {"statusCode": 500, "body": json.dumps({"error": "Query failed", "state": state})}

    # ✅ Get the query results
    results = athena_client.get_query_results(QueryExecutionId=query_execution_id)

    # ✅ Parse and return the results
    headers = [col["VarCharValue"] for col in results["ResultSet"]["Rows"][0]["Data"]]
    values = [col.get("VarCharValue", "NULL") for col in results["ResultSet"]["Rows"][1]["Data"]]

    query_result = dict(zip(headers, values))

    return {"statusCode": 200, "body": json.dumps({"message": "Query executed successfully", "result": query_result})}







# import boto3
# import json
#
# def lambda_handler(event, context):
#     athena_client = boto3.client("athena")
#
#     # ✅ Replacing CALL with the actual SQL query
#     failure_query = """
# ¬        SELECT 1
#     """
#
#     response = athena_client.start_query_execution(
#         QueryString=failure_query,
#         WorkGroup="clicksend-canary-workgroup",
#         ResultConfiguration={'OutputLocation': "s3://clicksend-canary-data/athena-query-results/"}
#     )
#
#     return {"QueryExecutionId": response["QueryExecutionId"]}
