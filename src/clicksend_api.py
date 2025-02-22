# src/clicksend_api.py
import datetime
import requests

import requests

def get_messages(api_username, api_key, start_epoch, end_epoch, page=1):
    url = "https://rest.clicksend.com/v3/messages"
    params = {
        "date_from": start_epoch,
        "date_to": end_epoch,
        "page": page
    }

    response = requests.get(url, auth=(api_username, api_key), params=params)

    if response.status_code == 404:
        return [], 404, None  # ✅ Return empty list, status code 404

    if response.status_code != 200:
        return None, response.status_code, None  # ✅ Return None, any error code

    response_data = response.json().get("data", {})

    return response_data.get("data", []), 200, response_data.get("last_page", page)

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