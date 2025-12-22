# Project Cogent: Vendor Spend Analysis Agent

## Workstream #2: Hybrid Search & Compliance Demo
This repository provides a production-ready reference implementation of an ADK Agent designed for vendor risk management. It demonstrates the Reasoning over Extracted Data (ROED) pattern using hybrid search.

**Status:** Production-Ready Reference Implementation
**Framework:** Google Agent Development Kit (ADK)
**Pattern:** Hybrid Search (Structured + Unstructured Data)

## 🎯 Overview

This project solves the "Source of Truth" problem in procurement. It correlates structured ERP data with unstructured legal contracts to find hidden risks.
- **Structured Data** (BigQuery) - Real-time vendor spend records and database renewal dates.
- **Unstructured Data** (Vertex AI Search) - PDF contracts containing legal clauses and actual termination dates.
- **AI Reasoning** (ADK Agent) - Cross-references both sources to detect "data traps" where the database contradicts the legal contract.

**The Value Proposition:**
Rather than building complex real-time connectors to legacy systems, this pattern extracts data once and enables powerful AI reasoning across both structured and unstructured sources.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Vendor Compliance Agent                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Orchestration: Correlates data across sources         │ │
│  │  Tools:                                                 │ │
│  │    1. get_high_value_vendors (BigQuery)                │ │
│  │    2. check_contract_compliance (Vertex AI Search)     │ │
│  │    3. check_contract_expiration (Cross-reference)      │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────┬────────────────────┘
                       │                  │
           ┌───────────▼──────────┐  ┌───▼──────────────────┐
           │   BigQuery           │  │ Vertex AI Search     │
           │   Dataset            │  │ Datastore            │
           ├──────────────────────┤  ├──────────────────────┤
           │ 50 Vendor Records    │  │ 20 PDF Contracts     │
           │ - Vendor ID          │  │ - Indemnification    │
           │ - Annual Spend       │  │ - Warranties         │
           │ - DB Renewal Date    │  │ - Termination Dates  │
           │ - Status             │  │ - Legal Clauses      │
           └──────────────────────┘  └──────────────────────┘
```

## ✨ Key Features

### The "Data Trap" - Risk Detection Demo
The mock data includes a specific scenario to test the agent's reasoning capabilities:
- **Vendor:** Apex Logistics (ID 99)
- **ERP Database:** Lists status as "Active" with a renewal date of 2027-01-01.
- **Legal Contract:** Explicitly states the agreement terminates on December 31, 2024.
- **Result:** The agent identifies that the company is currently paying a vendor ($200M/year) whose legal contract has already expired, despite what the ERP system claims.

This demonstrates real-world scenarios where:
- Legacy systems have outdated data
- Manual entry errors occur
- Multi-system synchronization fails
- Fraud or unauthorized spending happens

## 🚀 Quick Start

**Prerequisites**: 
Google Cloud Project with billing enabled.
`gcloud` CLI authenticated (`gcloud auth login`).
Python 3.10+ with `uv` installed.

### Installation & Deployment

```bash
# 1️⃣ Clone and install dependencies
git clone <repo-url>
cd project-cogent-2
make install

# 2️⃣ Setup Infrastructure (~5-10 mins)
# This creates BigQuery datasets and Vertex AI Search datastores
gcloud config set project YOUR-PROJECT-ID
make infra

# 3️⃣ Run the agent
make playground
```

**That's it!** The agent will analyze vendors and detect the contract expiration trap.

> **Note**: `make infra` automatically detects your project from `gcloud config`. You can also set `PROJECT_ID` environment variable to override.

### Alternative Testing Options
```bash
# Verbose output showing all tool calls
uv run python tests/test_agent_verbose.py

# Full integration test suite
pytest tests/integration/test_agent.py -v
```

## 📊 Sample Analysis

### Sample Query
> "Analyze all vendors with spend over $100M. Does the legal paperwork match our system records?"

### Expected Output
```
⚠️  CRITICAL ALERT: CONTRACT EXPIRATION MISMATCH!
============================================================
VENDOR: Apex Logistics (ID 99)
ERP Renewal Date: 2027-01-01 (In 2 years)
Contract PDF Date: 2024-12-31 (EXPIRED)

RISK: High-spend ($200M) activity detected on an expired contract.
REASON: Database shows "Active" but PDF clause 4.2 mandates auto-termination.
============================================================
```

## 📁 Project Structure

```
project-cogent-2/
├── app/
│   ├── agent.py                      # ADK Agent logic & instructions
│   └── tools.py                      # BQ & Vertex AI Search tool definitions
├── infra/
│   ├── data/                         # Raw CSVs and Contract PDFs
│   │   ├── structured/               # vendor_spend.csv
│   │   └── contracts/                # Generated PDFs
│   ├── scripts/                      # Hydration scripts for GCP services
│   │   ├── generate_contracts.py     # PDF generation
│   │   ├── setup_bigquery.py         # BQ hydration
│   │   └── setup_vertex_ai_search.py # VAIS hydration
│   ├── Makefile                      # Infrastructure automation
│   └── README.md             
├── tests/
│   ├── integration/                  # E2E "Trap Detection" tests   
│   │   └── test_agent.py             # E2E test with trap detection
│   └── test_agent_verbose.py         # Debug mode to see tool reasonings
└── README.md                         # This file
```

## 📚 Documentation

- **Infrastructure Setup:** [infra/README.md](infra/README.md)
- **ADK Documentation:** https://github.com/google/adk-python
- **Vertex AI Search:** https://cloud.google.com/generative-ai-app-builder

## 🐛 Troubleshooting

### Common Issues

**1. "No vendors found" error**
```bash
bq query --use_legacy_sql=false \
  "SELECT COUNT(*) FROM \`$PROJECT_ID.vendor_spend_dataset.vendor_spend\`"
```
Expected: 50

**2. "No contract documents found"**

Verify the Vertex AI Search datastore exists:
```bash
# Check datastore status
uv run python infra/scripts/check_datastore.py

# Check infrastructure metadata
cat infra/infrastructure_metadata.json
```

If documents are missing, wait 10-15 minutes for initial indexing after running `make infra`.

**3. Agent doesn't detect the trap**

Run the verbose test to see all tool calls:
```bash
uv run python tests/test_agent_verbose.py
```

The agent should:
- Call `get_high_value_vendors` to retrieve vendors from BigQuery
- Call `search_contracts` multiple times for each vendor
- Flag expired contracts with ⚠️ CRITICAL ALERT messages

## 🎯 Success Criteria

After running this demo, you should see:

✅ **The Main Trap Detected**: Apex Logistics ($200M spend)
- Database shows: renewal_date = 2027-01-01 (future), status = Active
- Contract PDF shows: "terminate automatically on December 31, 2024"
- Agent flags: ⚠️ CRITICAL ALERT - contract expired nearly a year ago

✅ **Additional Findings**:
- Alpha Systems Inc - expired Oct 2025
- Premier Logistics Inc - expired Dec 2025
- Zeta Corporation - expires in 4 days

✅ **Hybrid Search Working**:
- BigQuery provides structured vendor data (spend, renewal dates)
- Vertex AI Search retrieves unstructured contract terms (actual termination dates)
- Agent reasoning compares both sources to detect discrepancies

## 🧼 Cleanup
# To avoid ongoing charges for Vertex AI Search and BigQuery storage:

```bash
make destroy
```
