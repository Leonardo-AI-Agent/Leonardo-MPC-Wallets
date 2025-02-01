import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

BASE_URL = os.getenv("BASE_URL", "https://api.cdp.coinbase.com")
API_KEY_NAME = os.getenv("API_KEY_NAME")
API_KEY_PRIVATE = os.getenv("API_KEY_PRIVATE")

if not API_KEY_NAME or not API_KEY_PRIVATE:
    raise ValueError("Both API_KEY_NAME and API_KEY_PRIVATE must be set in the .env file!")
