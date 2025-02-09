import os
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

    def get_sms_history(self, **kwargs):
        """
        Retrieves SMS history from a single API call using the ClickSend SDK.
        Returns:
            A list of SMS messages extracted from the 'data' key of the response.
        """
        try:
            api_response = self.sms_api.sms_history_get(**kwargs)
            # If the response is an SDK model, convert it to a dict.
            if hasattr(api_response, "to_dict"):
                api_response = api_response.to_dict()
            if not isinstance(api_response, dict):
                raise ValueError("Unexpected response format from ClickSend API")
            return api_response.get("data", [])
        except ApiException as e:
            print(f"Exception when calling SMSApi->sms_history_get: {e}")
            raise

    def get_all_sms_history(self, **kwargs):
        """
        Retrieves SMS history across all pages by automatically paginating
        through the results.

        Assumes that the API response contains:
          - 'current_page': the current page number.
          - 'last_page': the total number of pages.
          - 'data': the list of SMS messages for that page.

        Returns:
            A combined list of SMS messages from all pages.
        """
        all_messages = []
        page = 1
        while True:
            response = self.sms_api.sms_history_get(page=page, **kwargs)
            if hasattr(response, "to_dict"):
                response = response.to_dict()
            if not isinstance(response, dict):
                raise ValueError("Unexpected response format from ClickSend API")
            # Extract messages from the 'data' key.
            page_messages = response.get("data", [])
            all_messages.extend(page_messages)

            # Check pagination details.
            current_page = response.get("current_page", page)
            last_page = response.get("last_page", current_page)

            # Validate next_page_url if there is another page.
            if current_page < last_page:
                expected_next_url = f"/?page={current_page + 1}"
                actual_next_url = response.get("next_page_url")
                if actual_next_url != expected_next_url:
                    raise ValueError(
                        f"Unexpected next_page_url: expected {expected_next_url}, got {actual_next_url}"
                    )

            if current_page >= last_page:
                break
            page += 1

        return all_messages
