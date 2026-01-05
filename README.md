# m1-aws-data-lake

# AWS Data Lake: OpenAQ Ingestion Pipeline

![Status](https://img.shields.io/badge/Status-In%20Progress-yellow)
![Terraform](https://img.shields.io/badge/IaC-Terraform-purple)
![AWS](https://img.shields.io/badge/Cloud-AWS-orange)

## Project Overview
This project establishes a Serverless Data Lake on AWS. It ingests air quality data from the OpenAQ API, stores it in an S3 RAW layer in Parquet format, and makes it analyzable via Amazon Athena.

## Architecture
* **Source:** OpenAQ REST API
* **Ingestion:** AWS Lambda (Python + Boto3)
* **Storage:** Amazon S3 (Partitioned, Parquet format)
* **Analytics:** Amazon Athena (SQL)
* **Infrastructure:** Terraform

## Project Structure
```text
.
├── .github/              # PR Templates and Workflows
├── lambda/               # Python source code for ingestion
├── sql/                  # Athena SQL queries for analysis
├── terraform/            # Infrastructure as Code
│   └── sandbox/          # Initial infrastructure tests
├── .gitignore
└── README.md

```

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
