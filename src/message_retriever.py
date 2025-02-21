from src.clicksend_api import fetch_all_messages
from src.storage import store_messages

def fetch_and_store_all_messages(api_username, api_key, start_time, end_time):
    for messages in fetch_all_messages(api_username, api_key, start_time, end_time):
        store_messages(messages)