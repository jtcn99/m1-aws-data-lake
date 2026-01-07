import os
import logging
import json
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class Config:
    def __init__(self):
        # 1. Environment Variables
        self.bucket_name = os.environ.get('BUCKET_NAME')
        self.api_url = os.environ.get('API_URL', "")
        self.secret_name = os.environ.get('SECRET_NAME', "")
        self.region_name = os.environ.get('AWS_REGION', "")

        self.s3_prefix = "openaq/"

        # 2. Fetch the API Key using your snippet logic
        self.api_key = self._get_secret(self.secret_name, self.region_name)

        if not self.bucket_name:
            raise ValueError("Environment variable 'BUCKET_NAME' is missing.")

    def _get_secret(self, secret_name, region_name):
        """
        Retrieves the secret string from AWS Secrets Manager.
        """
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name  # Now it uses the variable passed from __init__
        )

        try:
            get_secret_value_response = client.get_secret_value(
                SecretId=secret_name  # Now it uses the variable passed from __init__
            )
        except ClientError as e:
            raise e

        secret = get_secret_value_response['SecretString']

        return secret

    def get_api_headers(self):
        """Returns headers with API Key if available."""
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    def get_api_params(self):
        """Returns default query parameters for the API."""
        return {
            "limit": 100,
            "page": 1,
        }