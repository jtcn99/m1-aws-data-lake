terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Wir nutzen explizit das Profil, das wir gerade angelegt haben
provider "aws" {
  region  = "eu-central-1"
  profile = "openaq-project"
}

# Test: Wir fragen AWS: "Wer bin ich?" (Liest nur Daten, erstellt nichts)
data "aws_caller_identity" "current" {}

# Output: Zeige die Account-ID an, wenn es geklappt hat
output "connected_account_id" {
  value = data.aws_caller_identity.current.account_id
}