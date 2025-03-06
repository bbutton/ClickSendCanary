import boto3
import os
import json
import time
import traceback

from src.email_alert import send_alert_email

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

    try:
        response = athena_client.start_query_execution(
            QueryString=failure_query,
            WorkGroup=os.environ["ATHENA_WORKGROUP"]
        )
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

    results = athena_client.get_query_results(QueryExecutionId=query_execution_id)

    headers = [col["VarCharValue"] for col in results["ResultSet"]["Rows"][0]["Data"]]
    values = [col.get("VarCharValue", "NULL") for col in results["ResultSet"]["Rows"][1]["Data"]]

    query_result = dict(zip(headers, values))

    source_email = os.getenv("SES_SOURCE_EMAIL")
    alert_recipients = os.getenv("ALERT_RECIPIENTS").split(",")

    config = {}
    config["source_email"] = source_email
    config["recipients"] = [email.strip() for email in alert_recipients if email.strip()]

    try:
        ses_client = boto3.client("ses", region_name="us-east-1")
        email_response = send_alert_email(query_result, config, ses_client)
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": "Failed to send alert email", "exception": str(e)})}

        error_details = traceback.format_exc()  # Captures full error details
        print(f"❌ ERROR: {error_details}")  # Prints entire error log for debugging

        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e), "stack_trace": error_details})  # Returns full trace
        }

    return {"statusCode": 200, "body": json.dumps({"message": "Function executed successfully", "result": results})}
