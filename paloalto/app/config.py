
import os
from pathlib import Path

from dotenv import load_dotenv

# Load the project .env explicitly so debugger/Functions cwd does not matter.
DOTENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=DOTENV_PATH)

PANORAMA_URL = os.getenv("PANORAMA_URL")  # https://panorama.company.com
KEYVAULT_URL = os.getenv("KEYVAULT_URL")  # https://<kv>.vault.azure.net/
TENANT_ID=os.getenv("TENANT_ID")
CLIENT_ID=os.getenv("CLIENT_ID")
CLIENT_SECRET=os.getenv("CLIENT_SECRET") 
