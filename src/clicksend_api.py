# src/clicksend_api.py
import os
import datetime
import requests
from src.time_utils import convert_to_epoch

import os

# ✅ Load dotenv only when running locally
if os.getenv("AWS_EXECUTION_ENV") is None:  # AWS Lambda sets this variable
    from dotenv import load_dotenv
    load_dotenv()

# ✅ Environment variables (works both locally & in Lambda)
CLICKSEND_API_URL = os.getenv("CLICKSEND_API_URL", "https://rest.clicksend.com/v3/sms/history")

def get_messages(api_username, api_key, start_epoch:int, end_epoch:int, page=1):
    url = CLICKSEND_API_URL
    params = {
        "date_from": start_epoch,
        "date_to": end_epoch,
        "page": page,
        "limit": 100
    }

    print(f"🔍 Sending request to ClickSend API:")
    print(f"🔗 URL: {url}")
    print(f"📅 Params: {params}")

    response = requests.get(url, auth=(api_username, api_key), params=params)

    print(f"📥 API Response Code: {response.status_code}")
    print(f"📜 API Response Body: {response.text}")

    if response.status_code != 200:
        return None, response.status_code, None

    response_data = response.json().get("data", {})

    return response_data.get("data", []), response.status_code, response_data.get("last_page", 1)


def fetch_all_messages(api_username, api_key, start_time:str, end_time:str):
    start_epoch = convert_to_epoch(start_time)
    end_epoch = convert_to_epoch(end_time)
    current_page = 1
    last_page = None  # ✅ Track last_page

    while last_page is None or current_page <= last_page:
        messages, status_code, last_page = get_messages(api_username, api_key, start_epoch, end_epoch, current_page)

        if messages is None:  # API error like 500
            yield None, status_code
            return  # Stop fetching on critical failure

        yield messages, status_code

        if status_code != 200 or not messages:  # Stop on failure or empty data
            return

        current_page += 1