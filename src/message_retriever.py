from src.clicksend_api import fetch_all_messages
from src.storage import store_messages

def fetch_and_store_all_messages(api_username, api_key, start_time, end_time):
    total_messages = 0

    message_iterator = fetch_all_messages(api_username, api_key, start_time, end_time)
    for item in message_iterator:
        messages, status_code = item
        if status_code in (500, 404):  # ✅ Exit immediately on 500 or 404
            return 0, status_code

        store_messages(messages)
        total_messages += len(messages)

    return total_messages, 200  # ✅ Return success if we stored any messages