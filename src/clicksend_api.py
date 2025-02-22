# src/clicksend_api.py
import os
import datetime
from dotenv import load_dotenv
import requests

# ✅ Explicitly load `.env` from the project root
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

CLICKSEND_API_URL = os.getenv("CLICKSEND_API_URL", "https://rest.clicksend.com/v3/sms/history")

def get_messages(api_username, api_key, start_epoch, end_epoch, page=1):
    url = CLICKSEND_API_URL
    params = {
        "date_from": start_epoch,
        "date_to": end_epoch,
        "page": page
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

def convert_to_epoch(date_string):
    dt = datetime.datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
    return int(dt.timestamp())

def fetch_all_messages(api_username, api_key, start_time, end_time):
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