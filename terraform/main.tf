# --- Helper: Random ID for uniqueness ---
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# --- KMS Encryption ---
resource "aws_kms_key" "datalake_key" {
  description             = "KMS Key for Data Lake Encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true
}

resource "aws_kms_alias" "datalake_key_alias" {
  name          = "alias/${var.project_name}-key"
  target_key_id = aws_kms_key.datalake_key.key_id
}

# --- S3 Bucket ---
resource "aws_s3_bucket" "raw_layer" {
  bucket        = "${var.project_name}-raw-${random_id.bucket_suffix.hex}"
  force_destroy = true

  tags = {
    Name    = "OpenAQ Raw Layer"
    Project = var.project_name
  }
}

# S3 Security Block
resource "aws_s3_bucket_public_access_block" "raw_layer_security" {
  bucket = aws_s3_bucket.raw_layer.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "raw_layer_block" {
  bucket = aws_s3_bucket.raw_layer.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 Encryption Link
resource "aws_s3_bucket_server_side_encryption_configuration" "raw_layer_encrypt" {
  bucket = aws_s3_bucket.raw_layer.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.datalake_key.arn
    }
  }
}


# --- Secrets Manager ---
resource "aws_secretsmanager_secret" "openaq_key" {
  name        = "openaq-api-key-${random_id.bucket_suffix.hex}"
  description = "API Key for OpenAQ Ingestion (Managed by Terraform)"
}

# --- Lambda Function ---

# Zip the 'src' folder
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../src"
  output_path = "${path.module}/lambda_function.zip"
}

resource "aws_s3_bucket_policy" "raw_layer_policy" {
  bucket = aws_s3_bucket.raw_layer.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        # Statement 1: Zugriff nur für die Lambda-Rolle erlauben
        Sid       = "AllowOnlyLambdaWrite"
        Effect    = "Allow"
        Principal = {
          AWS = aws_iam_role.lambda_role.arn
        }
        Action    = "s3:PutObject"
        Resource  = "${aws_s3_bucket.raw_layer.arn}/raw/openaq/*"
      },
      {
        # Statement 2: HTTPS erzwingen (Unverschlüsselten Transport verbieten)
        Sid       = "DenyNonSecureTransport"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          aws_s3_bucket.raw_layer.arn,
          "${aws_s3_bucket.raw_layer.arn}/*"
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false" # Verweigert Zugriff bei HTTP
          }
        }
      }
    ]
  })
}

resource "aws_lambda_function" "ingest_function" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "${var.project_name}-ingest"
  role             = aws_iam_role.lambda_role.arn

  handler          = "main.lambda_handler"
  runtime          = var.python_runtime
  timeout          = 60
  memory_size      = 512
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  layers = [var.lambda_layer_arn]

  environment {
    variables = {
      BUCKET_NAME = aws_s3_bucket.raw_layer.bucket
      API_URL     = "https://api.openaq.org/v3/locations"
      SECRET_NAME = aws_secretsmanager_secret.openaq_key.name
    }
  }
}