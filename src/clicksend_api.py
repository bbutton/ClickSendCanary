# src/clicksend_api.py
import datetime

def get_messages(page = 1):
    """
    Placeholder function to allow tests to run.
    Will be implemented properly once we see test failures.
    """
    pass

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