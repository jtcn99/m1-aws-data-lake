# providers.tf
# This file defines WHICH tools (providers) we are using.

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  region = "eu-central-1"
  # We do not specify a profile here, as we control this via the
  # environment variable (AWS_PROFILE) to keep the code neutral.
}