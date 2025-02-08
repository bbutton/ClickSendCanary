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
        Retrieves SMS history from a single API call using the ClickSend SDK.
        Returns:
            A list of SMS messages extracted from the 'data' key of the response.
        """
        try:
            api_response = self.sms_api.sms_history_get(**kwargs)

            # If it's bytes, decode it to a string.
            if isinstance(api_response, bytes):
                api_response = api_response.decode('utf-8')

            # If the response is a string, try to parse it as JSON.
            if isinstance(api_response, str):
                try:
                    api_response = json.loads(api_response)
                except json.JSONDecodeError:
                    # Fallback: use ast.literal_eval if JSON parsing fails.
                    api_response = ast.literal_eval(api_response)

            # If the response is an SDK model, convert it to a dict.
            if hasattr(api_response, "to_dict"):
                api_response = api_response.to_dict()

            # At this point, we expect a dict.
            if isinstance(api_response, dict):
                # Check if there's a "data" key.
                if "data" in api_response:
                    data_field = api_response["data"]
                    # If the "data" key contains a list, return it.
                    if isinstance(data_field, list):
                        return data_field
                    # If "data" is a dict that itself contains a "data" key,
                    # try to extract the list from there.
                    elif isinstance(data_field, dict) and "data" in data_field and isinstance(data_field["data"], list):
                        return data_field["data"]
                    else:
                        # Debug print: show the response so we can inspect its structure.
                        return []
                else:
                    # No "data" key exists—print out the response for debugging.
                    return []

            # Fallback: if it’s an object with a data attribute.
            if hasattr(api_response, "data"):
                result = api_response.data
                if hasattr(result, "to_dict"):
                    result = result.to_dict()
                if isinstance(result, dict) and "data" in result and isinstance(result["data"], list):
                    return result["data"]
                return result

            raise ValueError("Unexpected response format from ClickSend API")

        except ApiException as e:
            print(f"Exception when calling SMSApi->sms_history_get: {e}")
            raise
