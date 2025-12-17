# Vendor Spend Analysis Agent - Infrastructure Setup

This infrastructure setup provides a complete **Hybrid Search** demonstration combining:
- **Structured Data** (BigQuery) - Vendor spend records
- **Unstructured Data** (Vertex AI Search) - Contract PDFs
- **The Trap** - Detects expired contracts still marked as Active

## Overview

The infrastructure creates:
1. **BigQuery Dataset** with 50 vendor records (6 with spend >$100M)
2. **20 PDF Contracts** with varying compliance clauses
3. **GCS Bucket** for document storage
4. **Vertex AI Search Datastore** for contract indexing
5. **The Trap**: Vendor ID 99 (Apex Logistics) - $200M spend, Active status, but contract EXPIRED 2024-12-31

## Prerequisites

- Google Cloud Project with billing enabled
- `gcloud` CLI configured and authenticated
- Python 3.10+ with `pip` or `uv`
- Required GCP APIs enabled (auto-enabled by Makefile):
  - BigQuery API
  - Cloud Storage API
  - Vertex AI Search API
  - Discovery Engine API

## Quick Start

### 1. Set Your Project

```bash
export PROJECT_ID="your-gcp-project-id"
gcloud config set project $PROJECT_ID
```

### 2. Run Infrastructure Setup

From the `infra/` directory:

```bash
make infra PROJECT_ID=$PROJECT_ID
```

This single command will:
- Install Python dependencies
- Generate 20 PDF contracts
- Create GCS bucket and upload contracts
- Create BigQuery dataset and load vendor data
- Create Vertex AI Search datastore and index contracts

**Expected duration:** 5-10 minutes (Vertex AI indexing takes time)

### 3. Configure Your Agent

Set environment variables for the agent:

```bash
export GOOGLE_CLOUD_PROJECT=$PROJECT_ID
export BQ_DATASET_ID=vendor_spend_dataset
export BQ_TABLE_ID=vendor_spend
export DATA_STORE_ID=vendor-analysis-datastore
export DATA_STORE_REGION=us
```

## Data Details

### Mock Vendor Data (50 vendors)

- **Total Vendors**: 50
- **High-Value Vendors (>$100M)**: 6
  1. Premier Logistics Inc - $120M
  2. Precision Manufacturing - $150M
  3. Alpha Systems Inc - $175M
  4. Zeta Corporation - $130M
  5. Quantum Dynamics - $112M
  6. **Apex Logistics - $200M** ⚠️ THE TRAP

### The Trap: Apex Logistics (Vendor ID 99)

**Database Record:**
```
vendor_id: 99
vendor_name: Apex Logistics
total_spend_ytd: $200,000,000
status: Active
renewal_date: 2027-01-01  ← WRONG!
```

**Contract PDF (`Apex_Logistics_MSA.pdf`):**
- Section 2 (TERM AND TERMINATION) states:
- **"This agreement shall terminate automatically on December 31, 2024."**
- ✓ Contract is EXPIRED
- ✓ Marked with "CONFIDENTIAL" watermark

**The Issue:**
The database shows a future renewal date (2027), but the actual contract PDF shows the agreement terminated on 2024-12-31 (past). This represents a high-spend vendor operating without a valid contract.

### Contract Compliance Variations

The 20 PDF contracts include variations in key clauses:

**Indemnification Clause Types:**
- `standard`: Normal indemnification coverage
- `enhanced`: Comprehensive coverage with insurance requirements
- `risky`: Limited liability (red flag)
- `missing`: No indemnification clause (red flag)

**Warranty Clause Types:**
- `standard`: Normal product/service warranties
- `extended`: 5-year warranties with guarantees
- `limited`: "AS IS" with minimal warranty (red flag)
- `missing`: No warranty terms (red flag)

**Vendors with Compliance Risks:**
- Alpha Systems Inc (ID 12) - Missing indemnification
- Zeta Corporation (ID 18) - Missing warranty
- Quantum Dynamics (ID 38) - Risky indemnification, limited warranty
- CloudNine Services (ID 5) - Missing indemnification
- Orion Manufacturing (ID 45) - Missing indemnification, limited warranty

## Manual Setup Steps (if needed)

### Generate PDFs Only

```bash
make generate-pdfs
```

### Setup GCS Only

```bash
make setup-gcs PROJECT_ID=$PROJECT_ID
```

### Setup BigQuery Only

```bash
make setup-bq PROJECT_ID=$PROJECT_ID
```

### Setup Vertex AI Search Only

```bash
make setup-vais PROJECT_ID=$PROJECT_ID
```

## Verification

### Check BigQuery Data

```bash
bq query --use_legacy_sql=false \
  "SELECT vendor_id, vendor_name, total_spend_ytd, renewal_date, status
   FROM \`$PROJECT_ID.vendor_spend_dataset.vendor_spend\`
   WHERE total_spend_ytd > 100000000
   ORDER BY total_spend_ytd DESC"
```

### Check GCS Bucket

```bash
gsutil ls gs://$PROJECT_ID-vendor-analysis-contracts/contracts/
```

### Check Vertex AI Search Datastore

```bash
gcloud beta discovery-engine data-stores list \
  --location=us \
  --project=$PROJECT_ID
```

## Cleanup

To remove all created infrastructure:

```bash
# Delete BigQuery dataset
bq rm -r -f -d $PROJECT_ID:vendor_spend_dataset

# Delete GCS bucket
gsutil rm -r gs://$PROJECT_ID-vendor-analysis-contracts

# Delete Vertex AI Search datastore (requires manual confirmation)
gcloud beta discovery-engine data-stores delete vendor-analysis-datastore \
  --location=us \
  --project=$PROJECT_ID

# Clean generated PDFs
make clean
```

## Troubleshooting

### "Permission denied" errors

Ensure you have the following IAM roles:
- `roles/bigquery.dataEditor`
- `roles/bigquery.jobUser`
- `roles/storage.admin`
- `roles/discoveryengine.admin`

### Vertex AI Search indexing takes too long

Initial indexing can take 10-30 minutes. Check status with:

```bash
gcloud beta discovery-engine operations list \
  --location=us \
  --project=$PROJECT_ID
```

### BigQuery dataset already exists

The setup scripts will skip creation if resources already exist. To force recreation, delete the dataset first.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ADK Agent Application                     │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Vendor Compliance Agent (agent.py)                   │  │
│  │                                                        │  │
│  │  Tools:                                                │  │
│  │  1. get_high_value_vendors()  ──────┐                 │  │
│  │  2. check_contract_compliance() ───┐│                 │  │
│  │  3. check_contract_expiration() ───┼┼──> TRAP DETECT  │  │
│  └────────────────────────────────────┼┼─────────────────┘  │
│                                         ││                    │
└─────────────────────────────────────────┼┼───────────────────┘
                                           ││
                         ┌────────────────┼┘
                         │                 │
                         ▼                 ▼
              ┌──────────────────┐  ┌─────────────────────┐
              │   BigQuery       │  │ Vertex AI Search    │
              │   Dataset        │  │ Datastore           │
              ├──────────────────┤  ├─────────────────────┤
              │ vendor_spend     │  │ 20 PDF Contracts    │
              │ (50 records)     │  │ (Indexed)           │
              │                  │  │                     │
              │ Structured Data: │  │ Unstructured Data:  │
              │ - Vendor ID      │  │ - Indemnification   │
              │ - Spend Amount   │  │ - Warranties        │
              │ - DB Renewal Date│  │ - REAL Term Dates   │
              │ - Status         │  │ - Legal Clauses     │
              └──────────────────┘  └─────────────────────┘
```

## Next Steps

After infrastructure setup:

1. **Test the Agent**: Run `pytest tests/integration/test_agent.py` from the project root
2. **Try the Verbose Test**: Run `uv run python tests/test_agent_verbose.py` to see all tool calls
3. **Use ADK Web UI**: Run `make playground` from project root for interactive testing

## Support

For issues or questions:
- Check the main project README
- Review ADK documentation: https://github.com/google/adk-python
- See Vertex AI Search docs: https://cloud.google.com/generative-ai-app-builder/docs
