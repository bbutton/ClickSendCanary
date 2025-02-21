import os
import argparse
from src.message_retriever import fetch_and_store_all_messages

def main():
    parser = argparse.ArgumentParser(description="Fetch and store SMS messages from ClickSend.")
    parser.add_argument("--start-time", required=True, help="Start time in format YYYY-MM-DD HH:MM:SS")
    parser.add_argument("--end-time", required=True, help="End time in format YYYY-MM-DD HH:MM:SS")
    args = parser.parse_args()

    clicksend_username = os.getenv("CLICKSEND_USERNAME")
    clicksend_api_key = os.getenv("CLICKSEND_API_KEY")
    if not clicksend_username or not clicksend_api_key:
        print("Error: ClickSend credentials missing. Set CLICKSEND_USERNAME and CLICKSEND_API_KEY.")
        return

    fetch_and_store_all_messages(clicksend_username, clicksend_api_key, args.start_time, args.end_time)
    print("✅ Messages successfully fetched and stored in S3.")

if __name__ == "__main__":
    main()