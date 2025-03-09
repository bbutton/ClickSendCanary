import boto3
import os
import json
import time
import traceback
import logging

from src.email_alert import send_alert_email
from src.state_manager import StateManager

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """Main Lambda handler that orchestrates the failure detection and alerting process."""
    try:
        s3_client = boto3.client("s3")
        athena_client = boto3.client("athena")
        ses_client = boto3.client("ses", region_name="us-east-1")

        state_manager = StateManager(
            s3_client=s3_client,
            bucket_name=os.getenv("S3_BUCKET", "clicksend-canary-data")
        )

        query_result = execute_failure_detection_query(athena_client)
        logger.info(f"Query result: {query_result}")

        state_info = state_manager.process_state_change(query_result)
        if state_info["state_changed"]:
            logger.info(f"Alert state changed from {state_info['previous_state'].get('alert_level', 'UNKNOWN')} to {state_info['current_state']['alert_level']}. Sending notification.")

            email_config = prepare_email_config()

            enhanced_result = query_result.copy()
            enhanced_result["previous_alert_level"] = state_info["previous_state"].get("alert_level", "UNKNOWN")
            enhanced_result["state_changed"] = True

            email_response = send_alert_email(enhanced_result, email_config, ses_client)
            logger.info(f"Email alert sent for state change")
        else:
            logger.info(f"No state change detected. Current alert level: {state_info['current_state']['alert_level']}")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Function executed successfully",
                "state_changed": state_info["state_changed"],
                "current_state": state_info["current_state"]
            })
        }

    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error executing function: {error_details}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e),
                "stack_trace": error_details
            })
        }

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