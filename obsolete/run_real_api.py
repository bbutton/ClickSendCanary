#!/usr/bin/env python3
import os
import sys
import argparse
import datetime
from src.clicksend_monitor import ClicksendSMSProvider
from mysql_connector import MySQLConnector

def convert_to_epoch(date_string):
    """
    Converts a datetime string in the format "YYYY-MM-DD HH:MM:SS" to epoch seconds.
    """
    dt = datetime.datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
    return int(dt.timestamp())


def sanitize_int_fields(rows, int_fields=None, default=0):
    """
    Iterates through each row in the provided list and, for each field specified
    in int_fields, sets its value to `default` if it is None.

    :param rows: List of dictionaries, each representing a row of SMS data.
    :param int_fields: Optional list of field names to check. Defaults to
                       ['date', 'schedule', 'message_parts'].
    :param default: The value to assign if the field is None (default is -999).
    :return: The modified list of rows.
    """
    if int_fields is None:
        int_fields = ['date', 'schedule', 'message_parts']

    for row in rows:
        for field in int_fields:
            if field in row and row[field] is None:
                row[field] = default
    return rows

def main():
    # Set up argparse to capture start and end times.
    parser = argparse.ArgumentParser(description="Retrieve ClickSend SMS history.")
    parser.add_argument('--start', type=str, help="Start time (YYYY-MM-DD hh:mm:ss)", required=False)
    parser.add_argument('--end', type=str, help="End time (YYYY-MM-DD hh:mm:ss)", required=False)
    args = parser.parse_args()

    # Build kwargs based on provided command line arguments.
    kwargs = {}
    kwargs['limit'] = 100
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
        sanitize_int_fields(history)
        db = MySQLConnector()
        try:
            db.insert_data(history)
            print("Data inserted successfully")
        except Exception as ex:
            print("An error occurred:", ex)
        finally:
            print("closing database")
            db.close()

        # print("Returned SMS history:")
        # for item in history:
        #     print(item)

    except Exception as e:
        print("An error occurred:", e)


if __name__ == '__main__':
    main()