import boto3
import os
import json
import datetime
import traceback

class StateManager:
    """Manages alert state persistence and comparison using S3."""

    def __init__(self, s3_client, bucket_name=None, state_key=None, history_key=None):
        """Initialize the StateManager with S3 client and configuration."""
        self.s3_client = s3_client
        self.bucket = bucket_name or os.getenv("S3_BUCKET", "clicksend-canary-data")
        self.state_key = state_key or "alert_state/current_state.json"
        self.history_key = history_key or "alert_state/state_history.jsonl"

    # Precondition - state file has to already exist
    def get_previous_state(self):
        response = self.s3_client.get_object(Bucket=self.bucket, Key=self.state_key)

        previous_state = json.loads(response['Body'].read().decode('utf-8'))
        print(f"📊 Retrieved previous state: {previous_state}")

        return previous_state

    def update_current_state(self, new_state): # Stopped here
        try:
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=self.state_key,
                Body=json.dumps(new_state),
                ContentType="application/json"
            )
            print(f"💾 Updated current state in S3: {new_state}")
            return True
        except Exception as e:
            print(f"❌ Error updating current state: {str(e)}")
            return False

    def does_state_file_exist(self):
        response = self.s3_client.list_objects_v2(
            Bucket=self.bucket,
            Prefix=self.state_key,
            MaxKeys=1
        )
        return response.get('KeyCount', 0) > 0

    def does_history_file_exist(self):
        response = self.s3_client.list_objects_v2(
            Bucket=self.bucket,
            Prefix=self.history_key,
            MaxKeys=1
        )
        return response.get('KeyCount', 0) > 0

    def add_to_state_history(self, state_record):
        try:
            file_exists = self.does_history_file_exist()

            history_content = ""
            if file_exists:
                get_response = self.s3_client.get_object(Bucket=self.bucket, Key=self.history_key)
                history_content = get_response['Body'].read().decode('utf-8')

            updated_content = history_content + json.dumps(state_record) + "\n"

            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=self.history_key,
                Body=updated_content,
                ContentType="application/jsonl"
            )
            print(f"📝 Added state change to history: {state_record}")
            return True
        except Exception as e:
            print(f"❌ Error adding to state history: {str(e)}")
            return False

    def has_state_changed(self, current_state, previous_state):
        """Check if the alert level has changed between states."""
        current_level = current_state.get("alert_level")
        previous_level = previous_state.get("alert_level")

        changed = current_level != previous_level
        if changed:
            print(f"🚨 Alert state changed: {previous_level} → {current_level}")
        else:
            print(f"✓ Alert state unchanged: {current_level}")

        return changed

    def create_state_record(self, query_result):
        """Create a state record from query results."""
        current_time = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        return {
            "timestamp": current_time,
            "alert_level": query_result.get("alert_level", "UNKNOWN"),
            "total_messages": query_result.get("total_messages", "0"),
            "failed_messages": query_result.get("failed_messages", "0"),
            "failure_rate": query_result.get("failure_rate", "0.0")
        }

    def process_state_change(self, query_result):
        try:
            current_state = self.create_state_record(query_result)

            state_file_exists = self.does_state_file_exist()

            if state_file_exists:
                previous_state = self.get_previous_state()
                state_changed = self.has_state_changed(current_state, previous_state)
            else:
                # First time running - consider it a state change from "unknown"
                previous_state = {"alert_level": "UNKNOWN", "timestamp": "N/A"}
                state_changed = True

            # Update the current state in S3
            self.update_current_state(current_state)

            # Add to history if state changed
            if state_changed:
                self.add_to_state_history(current_state)

            return {
                "state_changed": state_changed,
                "current_state": current_state,
                "previous_state": previous_state
            }
        except Exception as e:
            raise StateError("Error processing state change", {"error": str(e)})

class StateError(Exception):
    """Exception raised for errors during state management."""

    def __init__(self, message, error_details=None):
        super().__init__(message)
        self.error_details = error_details
