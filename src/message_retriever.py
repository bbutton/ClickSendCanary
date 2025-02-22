from src.clicksend_api import fetch_all_messages
from src.storage import store_messages

def fetch_and_store_all_messages(api_username, api_key, start_time, end_time):
    total_messages = 0

    for messages, status_code in fetch_all_messages(api_username, api_key, start_time, end_time):
        messages = messages or []  # ✅ Ensure messages is always a list

        print(f"📥 Retrieved messages: {messages}, Status: {status_code}")

        if status_code in (500, 404):
            return 0, status_code

        if len(messages) > 0:  # ✅ Only store if there are actual messages
            store_messages(messages)
            total_messages += len(messages)

    print(f"📊 Total messages retrieved: {total_messages}")
    return total_messages, 200