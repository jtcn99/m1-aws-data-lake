# Module 1: AWS Data Lake Ingestion Pipeline (OpenAQ)
![Status](https://img.shields.io/badge/Status-In%20Progress-yellow)
![Terraform](https://img.shields.io/badge/IaC-Terraform-purple)
![AWS](https://img.shields.io/badge/Cloud-AWS-orange)


This project implements a serverless data ingestion pipeline on AWS. It fetches air quality data from the [OpenAQ API v3](https://docs.openaq.org/), transforms it into Parquet format, and saves it to an AWS S3 Data Lake.

The entire infrastructure is defined as code using **Terraform**.

## Architecture
* **Source:** OpenAQ API (v3)
* **Compute:** AWS Lambda (Python 3.10)
* **Storage:** Amazon S3 (Partitioned Parquet files)
* **Configuration:** AWS Secrets Manager
* **IaC:** Terraform

## 📂 Project Structure
```text
m1-aws-data-lake/
├── src/
│   ├── __init__.py   # Makes the folder a Python package
│   ├── main.py       # Lambda handler
│   ├── etl.py        # Logic for fetching & transforming data
│   ├── config.py     # Configuration & Secrets Manager logic
│   └── requirements.txt
├── terraform/
│   ├── main.tf       # Lambda, S3, Secrets Manager resources
│   ├── iam.tf        # Permissions & Roles
│   ├── providers.tf  # AWS Provider configuration
│   ├── variables.tf  # Variable definitions
│   └── terraform.tfvars (DO NOT COMMIT THIS FILE)
└── README.md

```

## 🚀 Prerequisites

Before you start, ensure you have the following installed:

* [Python 3.10+](https://www.python.org/downloads/)
* [Terraform](https://developer.hashicorp.com/terraform/install)
* [AWS CLI](https://aws.amazon.com/cli/) (configured with `aws configure`)
* An [OpenAQ API Key](https://openaq.org/)

## 🛠️ Setup Instructions

### 1. Python Environment

Create a virtual environment and install dependencies.

```powershell
# Windows
python -m venv .venv
.\.venv\Scripts\Activate
pip install -r src/requirements.txt

```

### 2. Configure Terraform Provider

Ensure you have a `terraform/providers.tf` file to define the AWS connection:

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

```

### 3. Configure Secrets (Securely)

Create a `terraform.tfvars` file inside the `terraform/` folder to store your API Key.
**Note:** This file is ignored by `.gitignore` to prevent leaking secrets.

**File:** `terraform/terraform.tfvars`

```hcl
openaq_api_key = "your-raw-api-key-here-no-spaces"

```

### 4. Deploy Infrastructure

Initialize and apply the Terraform configuration.

```powershell
cd terraform
terraform init
terraform apply
# Type 'yes' when prompted

```

### 5. Package & Update Code

Whenever you change Python code in `src/`, you must re-zip and update the Lambda function.

**Windows PowerShell Command:**
Run this from the **project root** folder:

```powershell
# 1. Remove old zip (optional but recommended)
Remove-Item terraform\lambda_function.zip -ErrorAction SilentlyContinue

# 2. Zip the CONTENTS of src (flattened structure)
Compress-Archive -Path .\src\* -DestinationPath .\terraform\lambda_function.zip -Force

# 3. Upload the new zip to AWS
cd terraform
terraform apply -auto-approve
cd ..

```

## ✅ Verification

1. Go to the **AWS Console > Lambda > openaq-data-lake-ingest**.
2. Click the **Test** tab.
3. Click the orange **Test** button.
4. **Success Criteria:**
* Execution result: `Succeeded` (Green box).
* Check S3 Bucket: Go to `openaq-data-lake-raw-xxxx`.
* You should see a file path: `openaq/partition_date=YYYY-MM-DD/xyz.snappy.parquet`.



## 🔧 Troubleshooting

* **401 Unauthorized:** Check `terraform.tfvars` for hidden spaces in the key, run `terraform apply`, and check AWS Secrets Manager (Plaintext tab).
* **No module named 'src':** Ensure you zipped the *contents* of the folder (`src/*`), not the folder itself.
* **AccessDenied (S3):** Ensure `iam.tf` allows `s3:PutObject` on `${bucket_arn}/*` (note the asterisk).

```

```
## Data Lake Design (S3)

### Raw Layer
Der **Raw Layer** dient als "Source of Truth". Hier werden die Daten der OpenAQ-API unverändert (aber ins Parquet-Format konvertiert) abgelegt.
Es finden keine Aggregationen oder Löschungen statt, um historische Analysen jederzeit neu berechnen zu können.

* **Bucket-Namenskonvention:** `openaq-datalake-raw-[random-id]`
* **Sicherheit:**
  * **Block Public Access:** Aktiviert (kein öffentlicher Zugriff).
  * **Encryption:** Server-Side Encryption via KMS (Customer Managed Key) für maximale Kontrolle über den Datenschlüssel.

### Folder Structure (Prefixes)
Die Daten werden partitioniert abgelegt, um performante Abfragen zu ermöglichen (Hive-Style Partitioning).

**Schema:**
`raw/openaq/measurements/dt=YYYY-MM-DD/`

**Beispielpfad:**
`raw/openaq/measurements/dt=2026-01-05/openaq_data_20260105_1200.parquet`

### 🔒 Security & IAM (Least Privilege)
Das Projekt folgt konsequent dem **"Least Privilege" Prinzip**. Die Lambda-Funktion erhält keine pauschalen Admin-Rechte, sondern nur exakt die Berechtigungen, die für den Betrieb notwendig sind:

* **Rolle:** `openaq-lambda-execution-role`
* **S3 Write Access (Scoped):**
    * ✅ **Erlaubt:** Schreiben exklusiv in den Prefix `raw/openaq/*`.
    * ⛔ **Blockiert:** Zugriff auf den Bucket-Root oder andere Ordner.
    * *Warum?* Verhindert Datenchaos und schützt die Integrität anderer Datenprodukte im Data Lake.
* **KMS Encryption:**
    * ✅ **Erlaubt:** Nutzung des Customer Managed Keys (`kms:GenerateDataKey`).
    * *Warum?* Erforderlich, um Daten im verschlüsselten Ziel-Bucket sicher abzulegen (SSE-KMS).
* **Observability & Logging (Option B):**
    * ✅ **Erlaubt:** Erstellen von Log-Streams und Schreiben von Events nur in die eigene Log-Gruppe.
    * *Warum?* Ermöglicht präzises Debugging bei maximaler Isolation gegenüber anderen Services.
* **S3 Infrastructure Hardening:**
    * ✅ **Block Public Access:** Alle öffentlichen Zugriffswege sind hardwareseitig gesperrt.
    * ✅ **Secure Transport:** Zugriff ist nur via verschlüsseltem HTTPS möglich.

## Lokales Setup & Voraussetzungen

Die folgende Konfiguration ist notwendig, um das Projekt lokal auszuführen und Deployments durchzuführen.

### 1. AWS Konfiguration (Profil & Auth)

Das Projekt erwartet ein konfiguriertes AWS CLI Profil namens **`openaq-project`**.
Um Terraform und die CLI zu authentifizieren, ohne Credentials im Code zu speichern, nutzen wir Umgebungsvariablen.

**Einmaliges Setup:**

1. Access Keys für deinen IAM User erstellen (via AWS Konsole).
2. Lokal konfigurieren: `aws configure --profile openaq-project` (Region: `eu-central-1`).

**Vor der Arbeit (im Terminal):**
Damit Terraform das Profil findet, setze die Umgebungsvariable für deine aktuelle Session:

```powershell
# PowerShell (Windows / PyCharm Terminal)
$Env:AWS_PROFILE = "openaq-project"

# Verifizierung (Muss deine UserID zurückgeben)
aws sts get-caller-identity

```

### 2. Infrastructure as Code (Terraform)

Der Einstiegspunkt für die Infrastruktur liegt aktuell in der Sandbox.

```bash
cd terraform/sandbox

# Initialisierung der Provider
terraform init

# Planen der Änderungen (Dry-Run)
terraform plan

```

*Hinweis: Der `provider "aws"` Block im Code ist neutral gehalten. Er verlässt sich auf die Umgebungsvariable `AWS_PROFILE`, die im Schritt 1 gesetzt wurde.*

### 3. Quality Gates (Pre-Commit Hooks)

Dieses Repo nutzt `pre-commit`, um Terraform-Code automatisch zu formatieren (`terraform fmt`), bevor er committed wird.

**Installation (einmalig):**

```bash
# 1. Pre-commit Framework installieren
pip install pre-commit

# 2. Git Hooks im Repo aktivieren
pre-commit install

```

Ab jetzt wird bei jedem `git commit` automatisch geprüft, ob der Code sauber formatiert ist.

## Prerequisites Summary

* **AWS CLI:** Configured with profile `openaq-project`.
* **Terraform:** v1.x installed.
* **Python:** 3.9+ (for Lambda & hooks).
* **Git Hooks:** `pre-commit` installed and active.

---

**Owner:** jtamas@cloud-nation.de

**Last Updated:** 05.01.2026
