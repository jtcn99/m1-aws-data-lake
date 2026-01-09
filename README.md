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

## Security & IAM (Least Privilege)

Das Projekt folgt dem "Least Privilege" Prinzip. Die Lambda-Funktion erhält keine pauschalen Admin-Rechte, sondern nur exakt das, was sie benötigt.

### Lambda Execution Role
**Rolle:** `openaq-lambda-execution-role`

Die Berechtigungen sind strikt limitiert (Scoped Access):

1.  **S3 Write Access:**
    * ✅ Erlaubt: Schreiben in `raw/openaq/*`
    * ⛔ Blockiert: Schreiben in Root oder andere Folder.
    * *Warum?* Verhindert Datenchaos und versehentliches Überschreiben anderer Datenprodukte.

2.  **KMS Encryption:**
    * ✅ Erlaubt: Nutzung des Customer Managed Keys (`kms:GenerateDataKey`) zum Verschlüsseln neuer Objekte.
    * *Warum?* Ohne diese Berechtigung würde der Upload in den verschlüsselten Bucket fehlschlagen (Access Denied).

3.  **Observability:**
    * ✅ Erlaubt: Schreiben von Logs nach CloudWatch.
    * *Warum?* Ermöglicht Monitoring und Debugging der Pipeline.

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
