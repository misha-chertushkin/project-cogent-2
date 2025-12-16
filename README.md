# project-cogent-2
This repository provides reference implementation and ADK agent that covers Workstream #2 from project Cogent

## Vendor Spend Analysis Agent - Hybrid Search Demo

**Status:** Production-Ready Reference Implementation
**Framework:** Google Agent Development Kit (ADK)
**Pattern:** Reasoning over Extracted Data (Hybrid Search)

## 🎯 Overview

This project demonstrates a complete **Hybrid Search** solution that combines:
- **Structured Data** (BigQuery) - Vendor spend records from ERP systems
- **Unstructured Data** (Vertex AI Search) - Contract PDFs and legal documents
- **AI Reasoning** (ADK Agent) - Intelligent correlation and risk detection

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
The mock data includes a planted scenario:
- **Vendor:** Apex Logistics (ID 99)
- **Database Shows:** Active, $200M spend, Renewal Date: 2027-01-01
- **Contract PDF Shows:** "This agreement shall terminate automatically on December 31, 2024"
- **Result:** Agent detects the discrepancy and raises a CRITICAL ALERT

This demonstrates real-world scenarios where:
- Legacy systems have outdated data
- Manual entry errors occur
- Multi-system synchronization fails
- Fraud or unauthorized spending happens

## 🚀 Quick Start

**Prerequisites**: Google Cloud Project with billing enabled, `gcloud` CLI authenticated (`gcloud auth login`), Python 3.10+ with `uv`

### Three Simple Steps

```bash
# 1️⃣ Install dependencies
make install

# 2️⃣ Setup infrastructure (BigQuery + Vertex AI Search, ~5-10 mins)
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

## 📊 What the Demo Shows

### Sample Query
> "Analyze all vendors with annual spend over $100 million. For each vendor, check their contract compliance and verify that contract termination dates match our database renewal dates. Flag any discrepancies."

### Expected Output
```
⚠️  CRITICAL ALERT: CONTRACT EXPIRATION MISMATCH!
============================================================
Database shows renewal date: 2027-01-01 (FUTURE)
Contract PDF indicates termination in 2024 (PAST/EXPIRED)
Current date: 2025-12-16

RISK: Active vendor with high spend ($200M) operating under EXPIRED contract!
ACTION REQUIRED: Immediate contract review and legal verification needed.
============================================================
```

## 📁 Project Structure

```
ge-multi-search/
├── app/
│   ├── agent.py              # Main agent definition
│   └── tools.py              # Hybrid search tools (BQ + VAIS)
├── infra/
│   ├── data/
│   │   ├── structured/       # vendor_spend.csv
│   │   └── contracts/        # Generated PDFs
│   ├── scripts/
│   │   ├── generate_contracts.py    # PDF generation
│   │   ├── setup_bigquery.py        # BQ hydration
│   │   └── setup_vertex_ai_search.py # VAIS hydration
│   ├── Makefile              # One-command setup
│   └── README.md             # Infra documentation
├── tests/
│   ├── integration/
│   │   └── test_agent.py         # E2E test with trap detection
│   └── test_agent_verbose.py     # Verbose test showing tool calls
└── README.md                      # This file
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
