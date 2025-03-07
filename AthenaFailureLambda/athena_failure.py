import boto3
import os
import json
import time
import traceback

from src.email_alert import send_alert_email

def lambda_handler(event, context):
    """Main Lambda handler that orchestrates the failure detection and alerting process."""
    try:
        # Initialize AWS clients
        athena_client = boto3.client("athena")
        ses_client = boto3.client("ses", region_name="us-east-1")

        # Execute the Athena query to detect failures
        query_result = execute_failure_detection_query(athena_client)

        # Prepare email configuration
        email_config = prepare_email_config()

        # Send alert email
        send_alert_email(query_result, email_config, ses_client)

        return create_success_response(query_result)
    except AthenaQueryError as e:
        return create_error_response(e, 500, "Athena query failed")
    except EmailSendError as e:
        return create_error_response(e, 500, "Failed to send alert email")
    except Exception as e:
        return create_error_response(e, 500, "Unexpected error occurred")


def execute_failure_detection_query(athena_client):
    """Executes the SQL query to detect SMS failures and returns the parsed results."""
    try:
        query_execution_id = start_athena_query(athena_client)

        wait_for_query_completion(athena_client, query_execution_id)

        return parse_query_results(athena_client, query_execution_id)
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"❌ ERROR executing Athena query: {error_details}")
        raise AthenaQueryError(str(e), error_details)


def start_athena_query(athena_client):
    """Starts the Athena query execution and returns the execution ID."""
    failure_query = get_failure_detection_query()

    response = athena_client.start_query_execution(
        QueryString=failure_query,
        WorkGroup=os.environ["ATHENA_WORKGROUP"]
    )

    return response["QueryExecutionId"]


def get_failure_detection_query():
    """Returns the SQL query used to detect SMS failures."""
    return """
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


def wait_for_query_completion(athena_client, query_execution_id):
    """Waits for the Athena query to complete and raises an exception if it fails."""
    while True:
        query_status = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
        state = query_status["QueryExecution"]["Status"]["State"]

        if state in ["SUCCEEDED", "FAILED", "CANCELLED"]:
            break
        time.sleep(1)  # Small delay to avoid excessive API calls

    if state != "SUCCEEDED":
        raise AthenaQueryError(f"Query execution failed with state: {state}")


def parse_query_results(athena_client, query_execution_id):
    """Parses the Athena query results into a dictionary."""
    results = athena_client.get_query_results(QueryExecutionId=query_execution_id)

    headers = [col["VarCharValue"] for col in results["ResultSet"]["Rows"][0]["Data"]]
    values = [col.get("VarCharValue", "NULL") for col in results["ResultSet"]["Rows"][1]["Data"]]

    return dict(zip(headers, values))


def prepare_email_config():
    """Prepares the email configuration with source and recipients."""
    source_email = os.getenv("SES_SOURCE_EMAIL")
    alert_recipients_str = os.getenv("ALERT_RECIPIENTS", "")

    if alert_recipients_str:
        recipients = [email.strip() for email in alert_recipients_str.split(",") if email.strip()]
    else:
        recipients = []

    if not source_email or not recipients:
        raise EmailSendError("Missing required email configuration")

    return {
        "source_email": source_email,
        "recipients": recipients
    }


def create_success_response(query_result):
    """Creates a success response with the query results."""
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Function executed successfully",
            "result": query_result
        })
    }


def create_error_response(exception, status_code, message):
    """Creates an error response with details about the exception."""
    error_details = getattr(exception, 'error_details', traceback.format_exc())
    print(f"❌ ERROR: {error_details}")

    return {
        "statusCode": status_code,
        "body": json.dumps({
            "error": message,
            "details": str(exception),
            "stack_trace": error_details
        })
    }


class AthenaQueryError(Exception):
    """Exception raised for errors during Athena query execution."""

    def __init__(self, message, error_details=None):
        super().__init__(message)
        self.error_details = error_details


class EmailSendError(Exception):
    """Exception raised for errors during email sending."""

    def __init__(self, message, error_details=None):
        super().__init__(message)
        self.error_details = error_details