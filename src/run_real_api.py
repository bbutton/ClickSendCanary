#!/usr/bin/env python3
import os
import sys
import argparse
import datetime
from src.clicksend_monitor import ClicksendSMSProvider

def convert_to_epoch(date_string):
    """
    Converts a datetime string in the format "YYYY-MM-DD HH:MM:SS" to epoch seconds.
    """
    dt = datetime.datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
    return int(dt.timestamp())

def main():
    # Set up argparse to capture start and end times.
    parser = argparse.ArgumentParser(description="Retrieve ClickSend SMS history.")
    parser.add_argument('--start', type=str, help="Start time (YYYY-MM-DD hh:mm:ss)", required=False)
    parser.add_argument('--end', type=str, help="End time (YYYY-MM-DD hh:mm:ss)", required=False)
    args = parser.parse_args()

    # Build kwargs based on provided command line arguments.
    kwargs = {}
    if args.start:
        # Assuming the API expects a parameter called 'date_from'
        kwargs['date_from'] = convert_to_epoch(args.start)
    if args.end:
        # Assuming the API expects a parameter called 'date_to'
        kwargs['date_to'] = convert_to_epoch(args.end)

    # Instantiate the provider.
    provider = ClicksendSMSProvider()
    print("Fetching SMS history from ClickSend with parameters:", kwargs)

    try:
        # Retrieve all pages since no specific page is requested.
        history = provider.get_all_sms_history(**kwargs)
        print("Returned SMS history:")
        for item in history:
            print(item)
    except Exception as e:
        print("An error occurred:", e)


if __name__ == '__main__':
    main()