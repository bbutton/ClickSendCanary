import os
import json
import ast
import clicksend_client
from clicksend_client.rest import ApiException


class ClicksendSMSProvider:
    def __init__(self, username=None, api_key=None):
        """
        Initialize the provider. If username or api_key is not provided,
        the constructor attempts to load them from environment variables:
          - CLICKSEND_USERNAME
          - CLICKSEND_API_KEY
        """
        self.username = username or os.getenv("CLICKSEND_USERNAME")
        self.api_key = api_key or os.getenv("CLICKSEND_API_KEY")

        if not self.username or not self.api_key:
            raise ValueError("Missing Clicksend credentials: "
                             "CLICKSEND_USERNAME and CLICKSEND_API_KEY must be set")

        # Configure the SDK with credentials.
        self.configuration = clicksend_client.Configuration()
        self.configuration.username = self.username
        self.configuration.password = self.api_key

        self.api_client = clicksend_client.ApiClient(self.configuration)
        self.sms_api = clicksend_client.SMSApi(self.api_client)

    def _get_normalized_response(self, **kwargs):
        """
        Helper method that calls the ClickSend API and normalizes the response.
        It now supports responses that are either dictionaries, SDK objects (via to_dict),
        or plain JSON strings.

        Returns:
            A normalized dictionary containing the API response.
        """
        response = self.sms_api.sms_history_get(**kwargs)

        # If the response is a string, try to parse it as JSON.
        if isinstance(response, str):
            try:
                response = json.loads(response)
            except json.JSONDecodeError:
                # Fallback: use ast.literal_eval if JSON parsing fails.
                response = ast.literal_eval(response)

        # If the response is an SDK model, convert it to a dict.
        if hasattr(response, "to_dict"):
            response = response.to_dict()

        if not isinstance(response, dict):
            raise ValueError("Unexpected response format from ClickSend API")

        return response

    def get_sms_history(self, **kwargs):
        """
        Retrieves SMS history from a single API call using the ClickSend SDK.
        Returns:
            A list of SMS messages extracted from the 'data' key of the response.
        """
        response = self._get_normalized_response(**kwargs)
        return response.get("data", [])

    def get_all_sms_history(self, **kwargs):
        """
        Retrieves SMS history across all pages by automatically paginating
        through the results.

        Assumes that the API response contains:
          - 'current_page': the current page number.
          - 'last_page': the total number of pages.
          - 'data': the list of SMS messages for that page.
          - 'next_page_url': a relative URL indicating the next page,
                             e.g. "/?page=2".

        Returns:
            A combined list of SMS messages from all pages.

        Raises:
            ValueError: if the next_page_url in the response does not match
                        the expected value.
        """
        all_messages = []
        page = 1
        while True:
            response = self._get_normalized_response(page=page, **kwargs)

            current_page, last_page, page_messages = self._get_response_data(response)

            all_messages.extend(page_messages)

            print(f"{current_page}/{last_page} read")
            if current_page >= last_page:
                break
            page += 1

        return all_messages

    def _get_response_data(self, response):
        top_level_fields = response.get("data", [])
        current_page = top_level_fields.get("current_page", 1)
        last_page = top_level_fields.get("last_page", current_page)
        page_messages = top_level_fields.get("data", [])
        return current_page, last_page, page_messages
