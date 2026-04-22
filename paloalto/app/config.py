
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

PANORAMA_URL = os.getenv("PANORAMA_URL")  # https://panorama.company.com
KEYVAULT_URL = os.getenv("KEYVAULT_URL")  # https://<kv>.vault.azure.net/
TENANT_ID=os.getenv("TENANT_ID")
CLIENT_ID=os.getenv("CLIENT_ID")
CLIENT_SECRET=os.getenv("CLIENT_SECRET") 