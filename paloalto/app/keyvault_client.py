
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from app.config import KEYVAULT_URL
import logging

logger = logging.getLogger(__name__)

# Lazy initialization - client will be created when first needed
_client = None

def _get_client():
    """Get or create the Key Vault client lazily"""
    global _client
    if _client is None:
        logger.info(f"Initializing Key Vault client for: {KEYVAULT_URL}")
        try:
            # Uses managed identity in Azure and environment/Azure CLI credentials locally.
            credential = DefaultAzureCredential()
            _client = SecretClient(vault_url=KEYVAULT_URL, credential=credential)
        except Exception as e:
            logger.error(f"Failed to initialize Key Vault client: {e}")
            raise
    return _client

def get_secret(name: str) -> str:
    logger.debug(f"Retrieving secret: {name}")
    try:
        client = _get_client()
        value = client.get_secret(name).value
        logger.debug(f"Successfully retrieved secret: {name}")
        return value
    except Exception as e:
        logger.error(f"Failed to retrieve secret {name}: {e}")
        raise
