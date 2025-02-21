# src/clicksend_api.py
import datetime
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
        print(f"⚠️ API request returned 404: No messages found.")
        return {"messages": [], "current_page": 1, "last_page": 1}  # ✅ Return an empty response instead of None

    if response.status_code != 200:
        print(f"❌ API request failed with status {response.status_code}")
        return None

    response_data = response.json().get("data", {})

    return {
        "messages": response_data.get("data", []),
        "current_page": response_data.get("current_page", 1),
        "last_page": response_data.get("last_page", 1)
    }

def convert_to_epoch(date_string):
    dt = datetime.datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
    return int(dt.timestamp())

def fetch_all_messages(api_username, api_key, start_time, end_time):

    start_epoch = convert_to_epoch(start_time)
    end_epoch = convert_to_epoch(end_time)
    current_page = 1

    while True:
        response = get_messages(api_username, api_key, start_epoch, end_epoch, current_page)

        if not response or "data" not in response or "data" not in response["data"]:
            break

        yield response["data"]["data"]

        if response["data"]["current_page"] >= response["data"]["last_page"]:
            break

        current_page += 1