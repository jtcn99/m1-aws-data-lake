import json
from config import Config, logger
import etl

def lambda_handler(event, context):
    logger.info("Starting ingestion process...")
    try:
        # 1. Setup
        config = Config()

        # 2. Execution
        data = etl.fetch_data(config.api_url, config.get_api_params(), config.get_api_headers())

        if not data:
            return {"statusCode": 200, "body": "No data found."}

        df = etl.transform_data(data)
        etl.save_to_s3(df, config.bucket_name, config.s3_prefix)

        # 3. Success
        return {
            "statusCode": 200,
            "body": json.dumps(f"Successfully ingested {len(df)} rows.")
        }

    except Exception as e:
        logger.error(f"Critical workflow error: {str(e)}")
        raise e