import os
import json
from datetime import datetime, timedelta
from src.message_retriever import fetch_and_store_all_messages

# Conditionally load .env ONLY for local development
# ✅ Load dotenv only when NOT running in AWS Lambda
if os.getenv("AWS_EXECUTION_ENV") is None:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # ✅ Ignore if dotenv is missing in AWS Lambda

def lambda_handler(event, context):
    print("🚀 Lambda function started")  # ✅ Add this

    """
    AWS Lambda entry point.
    Expects an event with 'start_time' and 'end_time' parameters in YYYY-MM-DD HH:MM:SS format.
    """

    print("📌 Full Environment Variables Dump:")
    for key, value in os.environ.items():
        print(f"{key}={value}")

    # Extract parameters from the event
    start_time = event.get("start_time")
    end_time = event.get("end_time")

    # If missing, default to the last 10 minutes (for scheduled execution)
    if not start_time or not end_time:
        print("⚠️ No start_time or end_time provided, using last 10 minutes.")
        now = datetime.utcnow()
        start_time = (now - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
        end_time = now.strftime("%Y-%m-%d %H:%M:%S")

    print(f"📅 Fetching messages from {start_time} to {end_time}")  # ✅ Add this

    # Fetch ClickSend credentials from environment variables
    clicksend_username = os.getenv("CLICKSEND_USERNAME")
    clicksend_api_key = os.getenv("CLICKSEND_API_KEY")

    if not clicksend_username or not clicksend_api_key:
        print("❌ Missing required parameters for user and key!")  # ✅ Add this

        return {
            "statusCode": 500,
            "body": json.dumps("Error: Missing ClickSend credentials in environment variables")
        }

    # Call the function to retrieve messages and store them in S3
    messages_stored, error_code = fetch_and_store_all_messages(
        clicksend_username, clicksend_api_key, start_time, end_time
    )

    # Return the response
    print(f"📊 Retrieved {messages_stored} messages")  # ✅ Add this
    return {
        "statusCode": 200 if error_code == 200 else 500,
        "body": json.dumps({
            "message": "Lambda execution completed",
            "messages_stored": messages_stored,
            "error_code": error_code
        })
    }


# Allow execution from command line
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run ClickSend Retriever Locally")
    parser.add_argument("--start_time", required=True, help="Start time (YYYY-MM-DD HH:MM:SS)")
    parser.add_argument("--end_time", required=True, help="End time (YYYY-MM-DD HH:MM:SS)")
    args = parser.parse_args()

    response = lambda_handler({
        "start_time": args.start_time,
        "end_time": args.end_time
    }, None)

    print(response)
