import requests
import pandas as pd
import awswrangler as wr
from config import logger

def fetch_data(url: str, params: dict, headers: dict) -> list:
    logger.info(f"Fetching data from {url}...")
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)  # <--- Pass headers
        if response.status_code == 401:
            logger.error(f"401 RESPONSE TEXT: {response.text}")
        response.raise_for_status()
        results = response.json().get('results', [])
        return results
    except requests.exceptions.RequestException as e:
        logger.error(f"API Request failed: {e}")
        raise

def transform_data(results: list) -> pd.DataFrame:
    logger.info("Transforming data...")
    df = pd.json_normalize(results)

    if 'date.utc' in df.columns:
        df['date.utc'] = pd.to_datetime(df['date.utc'])
        df['partition_date'] = df['date.utc'].dt.date
    else:
        df['partition_date'] = pd.Timestamp.now().date()

    return df.astype(str)

def save_to_s3(df: pd.DataFrame, bucket: str, prefix: str):
    s3_path = f"s3://{bucket}/{prefix}"
    logger.info(f"Writing {len(df)} rows to: {s3_path}")
    wr.s3.to_parquet(
        df=df,
        path=s3_path,
        dataset=True,
        mode="append",
        partition_cols=["partition_date"]
    )