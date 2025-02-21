# src/storage.py

import pandas as pd
import io

def convert_to_parquet(messages):
    """
    Converts a list of message dictionaries into a Parquet file stored in memory.
    Returns the Parquet data as bytes.
    """
    df = pd.DataFrame(messages)
    parquet_buffer = io.BytesIO()
    df.to_parquet(parquet_buffer, index=False)
    return parquet_buffer.getvalue()

def store_messages(messages):
    """
    Placeholder function for storing messages.
    Will be implemented properly once we observe test failures.
    """
    pass

