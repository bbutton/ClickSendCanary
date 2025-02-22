from src.clicksend_api import fetch_all_messages
from src.storage import store_messages

def fetch_and_store_all_messages(api_username, api_key, start_time, end_time):
    total_messages = 0

    message_iterator = fetch_all_messages(api_username, api_key, start_time, end_time)
    print(f"Type of message_iterator: {type(message_iterator)}")

    for item in message_iterator:
        print(f"Fetched item: {item}")
        messages, status_code = item

        print(f"Inside loop: messages={messages}, status_code={status_code}")

        if status_code in (500, 404):  # ✅ Exit immediately on 500 or 404
            print("Exiting early due to error:", status_code)
            return 0, status_code

        store_messages(messages)
        print(f"Stored messages: {messages}")
        total_messages += len(messages)

    print(f"Total messages stored: {total_messages}")
    return total_messages, 200  # ✅ Return success if we stored any messages