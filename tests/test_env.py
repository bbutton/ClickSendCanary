import os
from dotenv import load_dotenv

# ✅ Explicitly load `.env` from the root folder
load_dotenv(dotenv_path=".env")

# ✅ Print environment variables to verify
print("🔍 CLICKSEND_USERNAME:", os.getenv("CLICKSEND_USERNAME"))
print("🔍 CLICKSEND_API_KEY:", os.getenv("CLICKSEND_API_KEY"))
print("🔍 CLICKSEND_API_URL:", os.getenv("CLICKSEND_API_URL"))
print("🔍 S3_BUCKET:", os.getenv("S3_BUCKET"))