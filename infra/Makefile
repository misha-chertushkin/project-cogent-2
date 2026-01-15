# Makefile for Vendor Spend Analysis Infrastructure Setup

# --- Configuration ---
PROJECT_ID ?= $(shell gcloud config get-value project)
REGION ?= us-central1
DATA_STORE_REGION ?= us
PROJECT_NAME ?= vendor-analysis
DATASET_ID ?= vendor_spend_dataset
TABLE_ID ?= vendor_spend
GCS_BUCKET ?= $(PROJECT_ID)-$(PROJECT_NAME)-contracts
DATA_STORE_ID ?= $(PROJECT_NAME)-datastore-v2

.PHONY: help sync-deps install-deps generate-pdfs setup-gcs setup-bq setup-vais infra clean dvc-pull d365-upload d365-download demo-e2e

help:
	@echo "Available targets:"
	@echo "  infra           - Run all setup steps (install-deps, setup-gcs, setup-bq, setup-vais)"
	@echo "  demo-e2e        - End-to-end demo: DVC pull → D365 upload → D365 download → GCP setup"
	@echo "  dvc-pull        - Pull contract PDFs and CSV from DVC remote storage"
	@echo "  d365-upload     - Upload contracts and data to Dynamics 365"
	@echo "  d365-download   - Download contracts and data from Dynamics 365"
	@echo "  setup-gcs       - Create GCS bucket and upload contracts"
	@echo "  setup-bq        - Create BigQuery dataset and load vendor data"
	@echo "  setup-vais      - Create Vertex AI Search datastore and index contracts"
	@echo "  clean           - Remove local generated files"

# --- Main Setup Workflow ---
infra: check-env enable-apis install-deps generate-pdfs setup-gcs setup-bq setup-vais
	@echo ""
	@echo "=============================================="
	@echo "✅ Infrastructure setup complete!"
	@echo "=============================================="
	@echo "Project ID:       $(PROJECT_ID)"
	@echo "GCS Bucket:       gs://$(GCS_BUCKET)"
	@echo "BigQuery Table:   $(PROJECT_ID).$(DATASET_ID).$(TABLE_ID)"
	@echo "VAIS Data Store:  $(DATA_STORE_ID)"
	@echo "=============================================="
	@echo "Next step: Wait 10-15 mins for VAIS indexing."

# --- Steps ---
check-env:
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "❌ Error: PROJECT_ID is not set. Use 'make infra PROJECT_ID=your-id'"; \
		exit 1; \
	fi

enable-apis:
	@echo "🚀 Enabling Google Cloud APIs..."
	gcloud services enable \
		bigquery.googleapis.com \
		storage.googleapis.com \
		discoveryengine.googleapis.com \
		aiplatform.googleapis.com

sync-deps:
	@echo "🔄 Syncing project dependencies (including DVC)..."
	@cd .. && uv sync
	@echo "✅ All project dependencies installed."

install-deps:
	@echo "Installing Python dependencies..."
	uv pip install -r requirements.txt || pip install -r requirements.txt

generate-pdfs:
	@echo "Generating PDF contracts..."
	uv run python scripts/generate_contracts.py || python scripts/generate_contracts.py

setup-gcs:
	@echo "Setting up GCS bucket: $(GCS_BUCKET)..."
	@# Create bucket if it doesn't exist
	@gsutil ls -b gs://$(GCS_BUCKET) 2>/dev/null || gsutil mb -p $(PROJECT_ID) -l $(REGION) gs://$(GCS_BUCKET)
	@echo "Uploading contracts to GCS..."
	gsutil -m cp -r data/contracts/*.pdf gs://$(GCS_BUCKET)/contracts/
	@echo "GCS setup complete. Bucket: gs://$(GCS_BUCKET)"

setup-bq:
	@echo "🚀 Setting up BigQuery..."
	@# Ensure PATH includes uv
	@export PATH="$$HOME/.local/bin:$$PATH" && \
	uv run python scripts/setup_bigquery.py --project_id $(PROJECT_ID)

setup-vais:
	@echo "Setting up Vertex AI Search datastore: $(DATA_STORE_ID)..."
	uv run python scripts/setup_vertex_ai_search.py --project_id $(PROJECT_ID) --data_store_id $(DATA_STORE_ID) --gcs_bucket $(GCS_BUCKET) --region $(DATA_STORE_REGION)
	@echo "Vertex AI Search setup complete. Data Store ID: $(DATA_STORE_ID)"

# --- End-to-End Demo Workflow ---
demo-e2e: check-env enable-apis sync-deps install-deps dvc-pull d365-upload d365-download setup-gcs setup-bq setup-vais
	@echo ""
	@echo "=============================================="
	@echo "✅ End-to-end demo setup complete!"
	@echo "=============================================="
	@echo "Project ID:       $(PROJECT_ID)"
	@echo "GCS Bucket:       gs://$(GCS_BUCKET)"
	@echo "BigQuery Table:   $(PROJECT_ID).$(DATASET_ID).$(TABLE_ID)"
	@echo "VAIS Data Store:  $(DATA_STORE_ID)"
	@echo "=============================================="
	@echo "Demo complete! Data journey:"
	@echo "  1. ✓ DVC → Local files"
	@echo "  2. ✓ Local files → Dynamics 365"
	@echo "  3. ✓ Dynamics 365 → Local files"
	@echo "  4. ✓ Local files → GCP (GCS, BigQuery, VAIS)"
	@echo "=============================================="

dvc-pull:
	@echo "📦 Pulling data from DVC..."
	@cd .. && uv run dvc pull
	@# Move files to the names the scripts expect immediately after pull
	@mkdir -p data/structured data/contracts
	@cp data/structured_to_upload/vendor_spend.csv data/structured/
	@cp -r data/contracts_to_upload/* data/contracts/
	@echo "✅ Data moved to standard paths for hydration scripts."

d365-upload:
	@echo "⬆️  Uploading contracts and data to Dynamics 365..."
	uv run python scripts/d365_backfill.py || python scripts/d365_backfill.py
	@echo ""
	@echo "=============================================="
	@echo "⏸️  PAUSE: Demo the Dynamics 365 UI"
	@echo "=============================================="
	@echo "Data has been uploaded to Dynamics 365."
	@echo "Please demo the D365 UI to show the data."
	@echo ""
	@read -p "Press Enter to continue after demoing D365 UI..." dummy

d365-download:
	@echo "⬇️  Downloading contracts and data from Dynamics 365..."
	uv run python scripts/d365_dump.py || python scripts/d365_dump.py
	@echo "D365 download complete."
	@echo "  - PDFs downloaded to: data/contracts/"
	@echo "  - CSV generated at: data/structured/vendor_spend.csv"

clean:
	@echo "🧹 Cleaning local generated files..."
	rm -f data/contracts/*.pdf
	rm -f data/structured/*.csv
	@echo "Clean complete."
