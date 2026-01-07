import os
import json
import logging
import requests
import pandas as pd
import awswrangler as wr  # AWS SDK for Pandas (simplifies S3 + Parquet)
from datetime import datetime

# Configure logging (to see errors in CloudWatch)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configuration
API_URL = "https://api.openaq.org/v2/measurements"
# Fetch data for Germany (DE), Limit 100, sorted by date
API_PARAMS = {
    "limit": 100,
    "page": 1,
    "offset": 0,
    "sort": "desc",
    "radius": 1000,
    "country_id": "DE",
    "order_by": "datetime"
}

# ENV
# Secret Manager
# Lamba wie übergeben

def lambda_handler(event, context):
    """
    AWS Lambda entry point.
    """
    logger.info("Starting ingestion process...")

    # 1. Retrieve Bucket Name from Environment Variables
    # (Injected via Terraform later)
    bucket_name = os.environ.get('BUCKET_NAME')
    if not bucket_name:
        raise ValueError("Environment variable BUCKET_NAME is missing!")

    path = f"s3://{bucket_name}/raw/openaq/measurements/"

    try:
        # 2. Fetch data from API
        logger.info(f"Fetching data from {API_URL}...")
        response = requests.get(API_URL, params=API_PARAMS)
        response.raise_for_status()  # Raise error if API response is not 200 OK

        data = response.json()
        results = data.get('results', [])

        if not results:
            logger.warning("No data received from API.")
            return {"status": "no_data"}

        logger.info(f"Received {len(results)} records.")

        # 3. Convert data to DataFrame
        df = pd.json_normalize(results)

        # Clean up data types (crucial for Parquet/Athena)
        # Extract date for partitioning
        df['date.utc'] = pd.to_datetime(df['date.utc'])
        df['partition_date'] = df['date.utc'].dt.date  # Creates YYYY-MM-DD

        # Convert everything to string to avoid nested JSON issues in Parquet
        df = df.astype(str)

        # 4. Write to S3 as Parquet (with Partitioning)
        # awswrangler handles KMS encryption automatically if the bucket enforces it.
        logger.info(f"Writing data to: {path}")

        wr.s3.to_parquet(
            df=df,
            path=path,
            dataset=True,  # Indicates this is part of a dataset
            mode="append",  # Append new data, do not overwrite
            partition_cols=["partition_date"]  # Automatically creates folder dt=YYYY-MM-DD
        )

        logger.info("Upload successful!")
        return {
            "statusCode": 200,
            "body": json.dumps(f"Successfully ingested {len(df)} rows.")
        }

    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        # Re-raise error to mark Lambda execution as failed in AWS
        raise e