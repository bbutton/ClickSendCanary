import json

# Define the base record template
base_record = {
    "direction": "out",
    "to": "+19019076984",
    "body": "MISSED COMM: SENSOR Hematology REF 28",
    "status": "Sent",
    "from": "+18335163193",
    "message_parts": 1,
    "message_price": "0.0108",
    "from_email": "temptrak@mlh.org"
}

# Filenames (Update these if needed)
file_names = {
    "message_id": "message_id.json",
    "sent_date": "sent_date.json",
    "status_code": "status_code.json",
    "status_text": "status_text.json"
}

# Load the data from the files
merged_data = {}
for key, filename in file_names.items():
    with open(filename, "r") as f:
        merged_data[key] = json.load(f)

# Ensure all lists have 50 values
num_records = 50
assert all(len(merged_data[key]) == num_records for key in merged_data), "Each file must have 50 values"

# Generate the full dataset
final_records = []
for i in range(num_records):
    record = base_record.copy()
    record["message_id"] = merged_data["message_id"][i]
    record["sent_date"] = merged_data["sent_date"][i]
    record["status_code"] = merged_data["status_code"][i]
    record["status_text"] = merged_data["status_text"][i]
    final_records.append(record)

# Save to output JSON file
output_file = "test_sms_data.json"
with open(output_file, "w") as f:
    json.dump(final_records, f, indent=4)

print(f"✅ Test dataset created: {output_file}")
