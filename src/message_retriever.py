# src/message_retriever.py
from src.clicksend_api import get_messages
from src.storage import store_messages

def fetch_and_store_messages():
    """
    Fetch messages from ClickSend and store them one page at a time.
    """

    response = get_messages()  # Fetch messages from ClickSend

    if not response or "data" not in response or "data" not in response["data"]:
        return  # Gracefully handle missing or malformed responses

 #   if "data" in response and "data" in response["data"]:
 #       messages = response["data"]["data"]
 #       store_messages(messages)  # Store the retrieved messages