variable "aws_region" {
  description = "AWS Region to deploy to"
  default     = "eu-central-1" # Frankfurt
}

variable "project_name" {
  description = "Base name for the project resources"
  default     = "openaq-data-lake"
}

variable "python_runtime" {
  description = "Python version for Lambda"
  default     = "python3.10"
}

variable "lambda_layer_arn" {
  description = "ARN for AWS SDK Pandas Layer (Python 3.10 / eu-central-1)"
  # Check https://github.com/aws/aws-sdk-pandas/releases for updates
  default     = "arn:aws:lambda:eu-central-1:336392948345:layer:AWSSDKPandas-Python310:12"
}

variable "max_pages" {
  description = "Number of pages to ingest. Set to -1 for unlimited."
  type        = string
  default     = "1"
}