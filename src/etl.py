import time

import requests
import pandas as pd
import awswrangler as wr
from config import logger


def fetch_all_data(url: str, base_params: dict, headers: dict, max_pages: int = 0) -> list:
    """
    Fetches all available data pages from the API using a persistent session.

    Iterates through paginated results until the API returns no more data or
    a partial page (indicating the end). Can be capped by 'max_pages' for testing.

    Args:
        url (str): The API endpoint URL.
        base_params (dict): Query parameters (must include 'limit').
        headers (dict): HTTP headers including authentication.
        max_pages (int, optional): Maximum number of pages to fetch.
                                   Defaults to 0 (fetch ALL available pages).

    Returns:
        list: A combined list of all result dictionaries fetched.
              Returns an empty list if the request fails or no data is found.
    """
    logger.info(f"Starting data fetch from {url}...")
    if max_pages > 0:
        logger.info(f"Safety brake enabled: stopping after {max_pages} pages.")
    else:
        logger.info("Auto-Pilot enabled: fetching ALL available data.")

    # 1. Initialize Session (The "Badge")
    # Performance: Re-uses the TCP connection for all page requests
    session = requests.Session()
    session.headers.update(headers)

    all_results = []
    page = 1

    # Extract the 'limit' (box size) so we know when a page is full or partial
    limit = base_params.get('limit', 1000)

    while True:
        # --- 1. Safety Brake Check ---
        # If max_pages is set (not 0) AND we have exceeded it, stop.
        if 0 < max_pages < page:
            logger.info(f"Reached max_pages limit ({max_pages}). Stopping.")
            break

        # --- 2. Prepare Request ---
        current_params = base_params.copy()
        current_params['page'] = page

        try:
            # Use the session (Headers are already attached)
            response = session.get(url, params=current_params, timeout=60)

            # Optional: Handle Rate Limiting (429) gracefully
            if response.status_code == 429:
                logger.warning("Rate limit hit. Sleeping for 5 seconds...")
                time.sleep(5)
                continue  # Retry the same page

            response.raise_for_status()

            data = response.json()
            results = data.get('results', [])

            # --- 3. Stop Condition: Empty Data ---
            if not results:
                logger.info("Received empty results. Fetching complete.")
                break

            all_results.extend(results)
            logger.info(f"Fetched page {page}: {len(results)} rows.")

            # --- 4. Stop Condition: Partial Page ---
            # If we asked for 1000 items but got 42, we are at the end.
            if len(results) < limit:
                logger.info(f"Received partial page ({len(results)} < {limit}). Fetching complete.")
                break

            page += 1

        except requests.exceptions.RequestException as e:
            # Log the full error but raise it so the Lambda fails (and alerts you)
            logger.error(f"Critical workflow error on page {page}: {e}")
            raise

    logger.info(f"Total rows fetched: {len(all_results)}")
    return all_results

def transform_data(results: list) -> pd.DataFrame:
    """
    Transforms raw JSON results into a flat DataFrame.

    Converts nested dictionaries and lists into strings to ensure
    compatibility with the Parquet file format while preserving
    numeric and date types for downstream analysis.

    Note for Data Analysts:
        To query nested fields in Amazon Athena, use the JSON functions.
        Example:
            SELECT json_extract_scalar(coordinates, '$.latitude') AS lat
            FROM your_table

    Returns:
        pd.DataFrame: A formatted DataFrame with string-cast columns.
    """
    if not results:
        return pd.DataFrame()

    logger.info("Transforming data...")
    df = pd.json_normalize(results)

    # Date handling
    if 'date.utc' in df.columns:
        df['date.utc'] = pd.to_datetime(df['date.utc'])
        df['partition_date'] = df['date.utc'].dt.date
    else:
        df['partition_date'] = pd.Timestamp.now().date()

    # Convert complex types (lists/dicts) to strings for Parquet compatibility
    # Instead of converting *everything* to string, only object columns
    for col in df.select_dtypes(include=['object']):
        df[col] = df[col].astype(str)

    return df

def save_to_s3(df: pd.DataFrame, bucket: str, prefix: str):
    """
    Writes the DataFrame to S3 in Parquet format with partitioning.

    Args:
        df: The data to save.
        bucket: Target S3 bucket name.
        prefix: S3 path prefix (folder structure).
    """
    if df.empty:
        logger.warning("DataFrame is empty. Skipping S3 write.")
        return

    s3_path = f"s3://{bucket}/{prefix}"
    logger.info(f"Writing {len(df)} rows to: {s3_path}")

    wr.s3.to_parquet(
        df=df,
        path=s3_path,
        dataset=True,
        mode="append",
        partition_cols=["partition_date"],
    )