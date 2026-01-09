import os
import json
import logging
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class Config:
    _secret_cache = None  # Class-level cache to persist across warm starts

    def __init__(self):
        self.bucket_name = os.environ.get('BUCKET_NAME')
        self.api_url = os.environ.get('API_URL')
        self.secret_name = os.environ.get('SECRET_NAME')
        self.region_name = os.environ.get('AWS_REGION', os.environ.get('AWS_DEFAULT_REGION'))
        self.s3_prefix = "raw/openaq/"
        # Default to 5 pages to prevent infinite loops during testing
        # Set to 0 or -1 in Env Vars if you want "Unlimited"
        self.max_pages = int(os.environ.get('MAX_PAGES', 5))

        if not self.bucket_name:
            raise ValueError("Environment variable 'BUCKET_NAME' is missing.")

        # Lazy load the API key
        self.api_key = self._get_secret_cached()

    def get_api_params(self):
        return {
            "limit": 1000,  # Always maximize this (from the doc)
            }

    def _get_secret_cached(self):
        """
        Retrieves the API key from the internal cache or AWS Secrets Manager.

        Uses caching to minimize latency and costs during warm Lambda invocations.
        """
        if Config._secret_cache:
            return Config._secret_cache

        if not self.secret_name:
            return None

        session = boto3.session.Session()
        client = session.client(service_name='secretsmanager', region_name=self.region_name)

        try:
            logger.info(f"Fetching secret: {self.secret_name}")
            response = client.get_secret_value(SecretId=self.secret_name)
            secret_str = response['SecretString']

            # PARSING FIX: Attempt to parse JSON, otherwise use raw string
            try:
                secret_dict = json.loads(secret_str)
                # Assumes the key inside the secret is 'api_key'. Adjust as needed.
                Config._secret_cache = secret_dict.get('api_key', secret_str)
            except json.JSONDecodeError:
                Config._secret_cache = secret_str

            return Config._secret_cache
        except ClientError as e:
            logger.error(f"Failed to retrieve secret: {e}")
            raise

    def get_api_headers(self):
        """
        Constructs the HTTP headers for the API request.

        Returns:
            dict: A dictionary containing the 'Accept' header and
                  the 'X-API-Key' if a secret has been successfully loaded.
        """
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers