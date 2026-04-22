import requests
import xmltodict
import time
import logging
import urllib3
from app.config import PANORAMA_URL
from app.keyvault_client import get_secret

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Disable SSL warnings for self-signed certificates (ONLY for testing!)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger.warning("SSL certificate verification is DISABLED. This is INSECURE and should only be used for testing!")

class PanoramaClient:

    def __init__(self):
        self.api_key = None

    def _generate_api_key(self):
        username = get_secret("panorama-username")
        password = get_secret("panorama-password")

        params = {
            "type": "keygen",
            "user": username,
            "password": password
        }

        logger.debug(f"Generating API key for Panorama: {PANORAMA_URL}")
        response = requests.get(f"{PANORAMA_URL}/api/", params=params, verify=False)  # SSL bypass
        logger.debug(f"API key response status: {response.status_code}")

        data = xmltodict.parse(response.text)
        return data["response"]["result"]["key"]

    def _get_api_key(self):
        if not self.api_key:
            self.api_key = self._generate_api_key()
        return self.api_key

    def _request(self, params):
        try:
            params["key"] = self._get_api_key()

            logger.debug(f"Making API request to {PANORAMA_URL}/api/ with params: {list(params.keys())}")
            response = requests.get(
                f"{PANORAMA_URL}/api/",
                params=params,
                verify=False  # SSL bypass
            )
            logger.debug(f"Response status: {response.status_code}")

            return xmltodict.parse(response.text)

        except Exception as e:
            logger.warning(f"API request failed, retrying with new key: {e}")
            # retry once with new key
            self.api_key = self._generate_api_key()
            params["key"] = self.api_key

            response = requests.get(
                f"{PANORAMA_URL}/api/",
                params=params,
                verify=False  # SSL bypass
            )

            return xmltodict.parse(response.text)

    def submit_log_query(self, query: str, log_type="traffic", nlogs=100):
        params = {
            "type": "log",
            "log-type": log_type,
            "query": query,
            "nlogs": str(nlogs),  # Limit results to prevent overwhelming responses
            "dir": "backward"  # Get most recent logs first
        }

        logger.info(f"Submitting {log_type} log query: {query}")
        data = self._request(params)
        job_id = data["response"]["result"]["job"]
        logger.info(f"Job submitted with ID: {job_id}")
        return job_id

    def wait_for_job(self, job_id: str, timeout=30):
        start = time.time()
        logger.info(f"Waiting for job {job_id} to complete...")

        while time.time() - start < timeout:
            params = {
                "type": "log",
                "action": "get",
                "job-id": job_id
            }

            data = self._request(params)
            status = data["response"]["result"]["job"]["status"]
            logger.debug(f"Job {job_id} status: {status}")

            if status == "FIN":
                logger.info(f"Job {job_id} completed successfully")
                return data

            time.sleep(2)

        logger.error(f"Job {job_id} timed out after {timeout} seconds")
        raise TimeoutError("Panorama job timeout")

    def query_logs(self, query: str, log_type="traffic"):
        logger.info(f"Querying {log_type} logs with query: {query}")
        job_id = self.submit_log_query(query, log_type)
        result = self.wait_for_job(job_id)

        logs = result["response"]["result"]["log"]["logs"]
        log_count = len(logs) if isinstance(logs, list) else 1
        logger.info(f"Retrieved {log_count} {log_type} log entries")

        return logs

    def get_config(self, xpath: str):
        params = {
            "type": "config",
            "action": "get",
            "xpath": xpath
        }

        logger.info(f"Retrieving Panorama config for xpath: {xpath}")
        data = self._request(params)
        return data.get("response", {}).get("result", {})
