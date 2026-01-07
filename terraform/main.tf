# main.tf
# This file defines WHAT is being built (the resources).

# --- Helper Resources ---

# Random ID for unique bucket names
# S3 bucket names must be globally unique. This generates a random suffix.
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# KMS Key (Our own master key for the vault)
resource "aws_kms_key" "datalake_key" {
  description             = "KMS Key for OpenAQ Data Lake Encryption"
  deletion_window_in_days = 30   # Waiting period before final deletion
  enable_key_rotation     = true # Automatically rotates the cryptographic key every year
}

# An alias (A readable name for the key)
resource "aws_kms_alias" "datalake_key_alias" {
  name          = "alias/openaq-datalake-key"
  target_key_id = aws_kms_key.datalake_key.key_id
}

# --- Storage (S3) ---

resource "aws_s3_bucket" "raw_layer" {
  # Name convention: project-raw-randomID
  bucket = "openaq-datalake-raw-${random_id.bucket_suffix.hex}"

  # Sandbox Mode: Allows Terraform to delete the bucket even if it contains files.
  # (Dangerous in production! Only use for testing.)
  force_destroy = true

  tags = {
    Name        = "OpenAQ Raw Layer"
    Environment = "Sandbox"
    Project     = "OpenAQ-DataLake"
  }
}

# --- Security & Encryption ---

# Block Public Access (No one from the outside can enter)
resource "aws_s3_bucket_public_access_block" "raw_layer_security" {
  bucket = aws_s3_bucket.raw_layer.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Enable Server-Side Encryption (Using KMS)
resource "aws_s3_bucket_server_side_encryption_configuration" "raw_layer_encrypt" {
  bucket = aws_s3_bucket.raw_layer.id

  rule {
    apply_server_side_encryption_by_default {
      # We use KMS instead of the standard AES256
      sse_algorithm = "aws:kms"
      # Reference to the key we created in Part 1
      kms_master_key_id = aws_kms_key.datalake_key.arn
    }
  }
}

# --- IAM Role & Permissions (The "ID Card" for Lambda) ---

# 1. The Role (The Identity itself)
# Defines "WHO" is allowed to assume this role -> The AWS Lambda Service.
resource "aws_iam_role" "lambda_role" {
  name = "openaq-lambda-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

# 2. The Policy (What is allowed with this ID card?)
resource "aws_iam_policy" "lambda_policy" {
  name        = "openaq-lambda-custom-policy"
  description = "Permissions for OpenAQ Ingestion: S3 Write, KMS Use, Logging"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # Rule A: Write Logs (Essential for debugging)
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      # Rule B: Write to S3 Bucket
      {
        Effect = "Allow"
        Action = "s3:PutObject"
        # CRITICAL: We allow writing ONLY to the prefix "raw/openaq/"
        # If Lambda tries to write elsewhere, it gets blocked.
        Resource = "${aws_s3_bucket.raw_layer.arn}/raw/openaq/*"
      },
      # Rule C: Use the KMS Key
      # Since the bucket is encrypted, Lambda needs permission to use the key
      # to seal the data (GenerateDataKey) when writing.
      {
        Effect = "Allow"
        Action = [
          "kms:GenerateDataKey",
          "kms:Decrypt"
        ]
        Resource = aws_kms_key.datalake_key.arn
      }
    ]
  })
}

# 3. Attachment (Glues the rules to the ID card)
resource "aws_iam_role_policy_attachment" "lambda_attach" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_policy.arn
}

# --- PART 5: Lambda Function & Application Logic ---

# 1. Zip the Code (Terraform packs your python file)
data "archive_file" "lambda_zip" {
  type        = "zip"
  # Wir gehen zwei Ordner hoch (../../) um in den lambda Ordner zu kommen
  source_file = "${path.module}/../../lambda/ingest.py"
  output_path = "${path.module}/lambda_ingest.zip"
}

# 2. Get the AWS Pandas Layer (Pre-built toolbox for Python 3.10)
# Documentation/Versions: https://github.com/aws/aws-sdk-pandas/releases
resource "aws_lambda_layer_version_permission" "allow_usage" {
  # ARN für eu-central-1 (Frankfurt) und Python 3.10
  layer_name     = "arn:aws:lambda:eu-central-1:336392948345:layer:AWSSDKPandas-Python310:12"
  action         = "lambda:GetLayerVersion"
  principal      = "*"
  statement_id   = "AllowUsage"
  version_number = 12
}

# 3. The Function itself
resource "aws_lambda_function" "ingest_function" {
  filename      = data.archive_file.lambda_zip.output_path
  function_name = "openaq-ingestion-service"
  role          = aws_iam_role.lambda_role.arn
  handler       = "ingest.lambda_handler" # filename.function_name

  # WICHTIG: Hier nutzen wir jetzt 3.10, passend zu deinem Laptop
  runtime       = "python3.10"

  timeout       = 60  # 60 Sekunden Zeit (Standard 3s ist zu kurz für Daten)
  memory_size   = 512 # Pandas braucht Arbeitsspeicher (512MB ist sicher)

  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  # Attach the "Toolbox" (Layer)
  layers = [
    "arn:aws:lambda:eu-central-1:336392948345:layer:AWSSDKPandas-Python310:12"
  ]

  # Environment Variables (Inject config into code)
  environment {
    variables = {
      BUCKET_NAME = aws_s3_bucket.raw_layer.bucket
    }
  }
}