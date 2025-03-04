import pandas as pd
import pyarrow.parquet as pq
import pyarrow as pa
import json
import time

# Load the JSON file
with open("test_sms_data.json", "r") as f:
    test_data = json.load(f)

# Get the current time (UTC) and set the latest timestamp to NOW
current_time = int(time.time())  # Current epoch time
earliest_time = current_time - 1800  # 30 minutes ago

# Distribute timestamps evenly over the last 30 minutes (newest first)
for i, msg in enumerate(test_data):
    msg["sent_date"] = current_time - (i * (1800 // len(test_data)))

# Convert JSON to Pandas DataFrame
df = pd.DataFrame(test_data)

# Convert DataFrame to Parquet
table = pa.Table.from_pandas(df)
parquet_filename = "test_sms_data.parquet"
pq.write_table(table, parquet_filename)

print(f"✅ Updated timestamps and converted JSON to Parquet: {parquet_filename}")

