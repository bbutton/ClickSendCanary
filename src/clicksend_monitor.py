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

    def get_sms_history(self, **kwargs):
        """
        Retrieves SMS history using the Clicksend SDK.
        Accepts any keyword arguments the SDK method supports.
        Returns:
            A list of SMS history items extracted from the paginated response.
        """
        try:
            api_response = self.sms_api.sms_history_get(**kwargs)

            # If the response is bytes, decode it to a string.
            if isinstance(api_response, bytes):
                api_response = api_response.decode('utf-8')

            # If the response is a string, try parsing it as JSON.
            if isinstance(api_response, str):
                try:
                    api_response = json.loads(api_response)
                except json.JSONDecodeError:
                    # Fallback: if it's a Python literal string with single quotes.
                    api_response = ast.literal_eval(api_response)

            # If the response has a to_dict() method (common with SDK models), convert it.
            if hasattr(api_response, "to_dict"):
                api_response = api_response.to_dict()

            # Now, assume we have a dictionary. The paginated response should have a "data" key.
            if isinstance(api_response, dict):
                return api_response.get("data", [])

            # Fallback: if we have an object with a data attribute.
            if hasattr(api_response, "data"):
                result = api_response.data
                if hasattr(result, "to_dict"):
                    result = result.to_dict()
                if isinstance(result, dict):
                    return result.get("data", [])
                return result

            raise ValueError("Unexpected response format from ClickSend API")

        except ApiException as e:
            print(f"Exception when calling SMSApi->sms_history_get: {e}")
            raise
