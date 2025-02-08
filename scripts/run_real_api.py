#!/usr/bin/env python3
import os
from src.clicksend_monitor import ClicksendSMSProvider

def main():
    try:
        # The provider will pick up the credentials from environment variables.
        provider = ClicksendSMSProvider()
        print("Fetching SMS history from ClickSend...")
        history = provider.get_sms_history()
        print("SMS History:")
        for msg in history:
            print(msg)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    main()
