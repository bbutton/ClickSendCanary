#!/usr/bin/env python3
import os
import sys

# Add the project root to sys.path so that 'src' can be imported.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.clicksend_monitor import ClicksendSMSProvider


def main():
    try:
        provider = ClicksendSMSProvider()
        print("Fetching SMS history from ClickSend...")
        history = provider.get_sms_history()

        # Debug output: show the type and full content of the returned data.
        print("Type of returned data:", type(history))
        print("Returned SMS history:")
        for item in history:
            print(item)
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == '__main__':
    main()
