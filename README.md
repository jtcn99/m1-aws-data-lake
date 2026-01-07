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
## Getting Started
Prerequisites
* AWS CLI configured with a valid profile

* Terraform installed (v1.x+)

* Python 3.9+

## CI/CD (GitHub Actions)
* Workflow: `.github/workflows/terraform.yml`
* Triggers: PRs and pushes to `main` that touch `terraform/`, plus manual runs
* Secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`
* Behavior: fmt/validate/plan on PRs, plan + apply on pushes to `main`


Owner: jtamas@cloud-nation.de 

Date: 05.01.2026
