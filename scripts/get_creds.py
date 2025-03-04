import json

# Read the AWS STS output from the file
with open("aws_creds.json", "r") as file:
    data = json.load(file)

# Extract credentials
access_key = data["Credentials"]["AccessKeyId"]
secret_key = data["Credentials"]["SecretAccessKey"]
session_token = data["Credentials"]["SessionToken"]

# Generate export commands
export_commands = f"""
export AWS_ACCESS_KEY_ID="{access_key}"
export AWS_SECRET_ACCESS_KEY="{secret_key}"
export AWS_SESSION_TOKEN="{session_token}"
"""

# Print the commands to be copied or executed
print(export_commands)

