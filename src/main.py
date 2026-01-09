import json

import etl
from config import Config, logger

# Global init to reuse resources across warm Lambda invocations
# Note: Exception handling is needed in case env vars are missing during import
try:
    config = Config()
except Exception as e:
    logger.critical(f"Global initialization failed: {e}")
    raise


def lambda_handler(event, context):
    if not config:
        return {"statusCode": 500, "body": "Configuration Error"}

    logger.info("Starting ingestion process...")

    try:
        # 1. Fetch (with pagination)
        data = etl.fetch_all_data(
            config.api_url,
            config.get_api_params(),
            config.get_api_headers(),
            max_pages=config.max_pages,
        )

        if not data:
            return {"statusCode": 200, "body": "No data found."}

        # 2. Transform
        df = etl.transform_data(data)

        # 3. Load
        etl.save_to_s3(df, config.bucket_name, config.s3_prefix)

        return {
            "statusCode": 200,
            "body": json.dumps(f"Successfully ingested {len(df)} rows."),
        }

    except Exception as e:
        logger.error(f"Workflow failed", exc_info=True)  # exc_info adds stack trace
        raise e
