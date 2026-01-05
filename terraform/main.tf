# main.tf
# This file defines WHAT is being built (the resources).

# --- PART 1: Helper Resources ---

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

# --- PART 2: Storage (S3) ---

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

# --- PART 3: Security & Encryption ---

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
