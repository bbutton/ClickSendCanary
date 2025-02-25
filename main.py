import os
import json
from src.message_retriever import fetch_and_store_all_messages

# Conditionally load .env ONLY for local development
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

def lambda_handler(event, context):
    """
    AWS Lambda entry point.
    Expects an event with 'start_time' and 'end_time' parameters in YYYY-MM-DD HH:MM:SS format.
    """

    # Extract parameters from the event
    start_time = event.get("start_time")
    end_time = event.get("end_time")

    if not start_time or not end_time:
        return {
            "statusCode": 400,
            "body": json.dumps("Error: Missing 'start_time' or 'end_time' in event payload")
        }

    # Fetch ClickSend credentials from environment variables
    clicksend_username = os.getenv("CLICKSEND_USERNAME")
    clicksend_api_key = os.getenv("CLICKSEND_API_KEY")

    if not clicksend_username or not clicksend_api_key:
        return {
            "statusCode": 500,
            "body": json.dumps("Error: Missing ClickSend credentials in environment variables")
        }

    # Call the function to retrieve messages and store them in S3
    messages_stored, error_code = fetch_and_store_all_messages(
        clicksend_username, clicksend_api_key, start_time, end_time
    )

    # Return the response
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
