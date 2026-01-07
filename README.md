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

## 🎯 When to Use This Demo

This repository is a reference implementation for **Hybrid Search Reasoning**. It is specifically designed for scenarios where transactional data (SQL) must be reconciled against unstructured ground truth (PDFs).

### ✅ Ideal Use Cases
* **Source of Truth Reconciliation:** Identifying discrepancies between a database (e.g., ERP renewal dates) and legal contracts (e.g., termination clauses).
* **Procurement & Compliance Audits:** Automating risk detection in high-value vendor relationships.
* **Heterogeneous Document Analysis:** Extracting insights from diverse legal papers that lack a standard template.

### 🚀 Key Value Prop
Unlike basic RAG, this agent doesn't just "find" information; it **reasons across systems** to detect data "traps" that traditional automation would miss.

> 📖 **[Read the Full 'When to Use' Guide](docs/WHEN_TO_USE.md)** for deep-dive discovery questions and strategic selling points.

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

### Two Demo Modes

### Option 1: Standard Demo (Synthetic Data)
### Four Simple Steps to Success

```bash
# 1️⃣ Install dependencies
uv sync

# 2️⃣ Setup infrastructure (generates PDFs, creates BigQuery + Vertex AI Search, ~5-10 mins)
gcloud config set project YOUR-PROJECT-ID
cd infra
make infra

# 3️⃣ Launch the Agent
uv run adk run app

# 4️⃣ Run the Demo
# Use the "Golden Queries" from PROMPTS.md to trigger the Apex Trap.

#### Option 2: End-to-End Demo (with Dynamics 365)

Use this to demonstrate the complete data journey from Dynamics 365 → GCP → Agent.

```bash
# 1️⃣ Install dependencies
uv sync

# 2️⃣ Configure Dynamics 365 credentials
cd infra
cp .env.example .env
# Edit .env with your D365 credentials
cd ..

# 3️⃣ Pull production data from DVC
dvc pull

# 4️⃣ Run end-to-end infrastructure setup
gcloud config set project YOUR-PROJECT-ID
cd infra
make demo-e2e

# This will:
# - Pull contract PDFs and CSV from DVC remote storage
# - Upload data to Dynamics 365 CRM
# - PAUSE for you to demo the D365 UI (press Enter to continue)
# - Download data back from Dynamics 365
# - Create BigQuery dataset and load vendor data
# - Create Vertex AI Search datastore and index contracts
# - Setup complete GCP infrastructure

# 5️⃣ Run the agent
cd ..
uv run adk run app
```

**That's it!** The agent will analyze vendors and detect the contract expiration trap.

🕹️ Pro-Tip: Open PROMPTS.md for a copy-paste list of high-impact queries to use during your live demo.

> **Note**: Both workflows automatically detect your project from `gcloud config`. You can also set `PROJECT_ID` environment variable to override.

### Alternative Testing Options
```bash
# Verbose output showing all tool calls
uv run python tests/test_agent_verbose.py

# Full integration test suite
pytest tests/integration/test_agent.py -v
```

## 📦 Data Management with DVC

This project uses [DVC (Data Version Control)](https://dvc.org) to manage datasets stored in Google Cloud Storage.

### End-to-End Demo Workflow

The `demo-e2e` target demonstrates a complete data journey:

```
DVC (GCS) → Local Files → Dynamics 365 → Local Files → GCP (BigQuery + VAIS)
```

**Step-by-step flow:**

1. **DVC Pull**: Downloads production data from GCS remote storage
   - `infra/data/contracts_to_upload/` - Contract PDFs ready for D365
   - `infra/data/structured_to_upload/vendor_spend.csv` - Vendor records

2. **D365 Upload**: Uploads data to Dynamics 365 CRM
   - Creates Account records with vendor metadata
   - Attaches contract PDFs as annotations
   - Creates Invoice records for spend tracking
   - **PAUSES** for demo of D365 UI

3. **D365 Download**: Extracts data back from Dynamics 365
   - Downloads to `infra/data/contracts/`
   - Generates CSV at `infra/data/structured/vendor_spend.csv`
   - Preserves original vendor IDs for consistency

4. **GCP Setup**: Creates cloud infrastructure
   - Uploads PDFs to GCS bucket
   - Loads CSV into BigQuery table
   - Indexes contracts in Vertex AI Search

### Manual DVC Operations

To manually pull data:

```bash
# Pull all tracked data
dvc pull

# Pull specific files
dvc pull infra/data/contracts_to_upload.dvc
dvc pull infra/data/structured_to_upload/vendor_spend.csv.dvc
```

### DVC Configuration

- **Remote Storage**: `gs://project-cogent-2-dvc/dvc-store`
- **Tracked Paths**:
  - `infra/data/contracts_to_upload/` - Original contract PDFs
  - `infra/data/structured_to_upload/vendor_spend.csv` - Original vendor data

> **Note**: You need access to the GCS bucket `project-cogent-2-dvc`. Ensure you're authenticated with `gcloud auth login` and have the necessary permissions.

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
├── app/                      # Core Agent Application
│   ├── agent.py              # Main ADK agent logic & reasoning
│   ├── config.py             # App configuration and environment mapping
│   ├── tools.py              # Hybrid search tool definitions (BQ + VAIS)
│   └── __init__.py           
├── docs/                     # Strategic & Sales Enablement
│   └── WHEN_TO_USE.md        # Discovery guide & customer use cases
├── evals/                    # Quality & Validation
│   └── scenarios.md          # 6 Detailed engineering test cases
├── infra/                    # Infrastructure & Data Hydration
│   ├── data/
│   │   ├── contracts_to_upload/     # [DVC] Original PDFs for D365 upload
│   │   ├── structured_to_upload/    # [DVC] Original CSV for D365 upload
│   │   ├── contracts/               # Downloaded/Generated contract PDFs
│   │   └── structured/              # Generated vendor_spend.csv
│   ├── scripts/              # Automation scripts
│   │   ├── check_datastore.py       # VAIS health check utility
│   │   ├── d365_backfill.py         # Upload data to Dynamics 365
│   │   ├── d365_dump.py             # Download data from Dynamics 365
│   │   ├── generate_contracts.py    # PDF document generation (synthetic)
│   │   ├── setup_bigquery.py        # BQ schema & data hydration
│   │   └── setup_vertex_ai_search.py # VAIS datastore & engine setup
│   ├── Makefile              # One-command automation (infra, demo-e2e)
│   ├── README.md             # Infrastructure-specific guide
│   ├── infrastructure_metadata.json
│   └── requirements.txt      # Infrastructure-specific dependencies
├── tests/                    # Test Suites
│   ├── integration/
│   │   └── test_agent.py         # E2E test for the "Apex Trap"
│   └── unit/
│       ├── test_agent_verbose.py # Log-heavy tool orchestration test
│       └── test_dummy.py
├── GEMINI.md                 # Project-specific AI notes
├── LICENSE                   # Apache 2.0 License
├── PROMPTS.md                # "Greatest Hits" Demo Menu
├── pyproject.toml            # Project metadata and dependencies
├── README.md                 # Main overview and Quick Start
└── uv.lock                   # Lockfile for reproducible environments
```

## 📚 Documentation

- **Infrastructure Setup:** [infra/README.md](infra/README.md)
- **ADK Documentation:** https://github.com/google/adk-python
- **Vertex AI Search:** https://cloud.google.com/generative-ai-app-builder
- **Demo Menu (Golden Queries):** [PROMPTS.md](./PROMPTS.md)
- **Engineering Test Scenarios:** [evals/scenarios.md](./evals/scenarios.md)

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
