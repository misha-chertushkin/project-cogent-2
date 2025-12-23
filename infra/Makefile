# Makefile for Vendor Spend Analysis Infrastructure Setup

# --- Configuration ---
PROJECT_ID ?= $(shell gcloud config get-value project)
REGION ?= us-central1
DATA_STORE_REGION ?= us
PROJECT_NAME ?= vendor-analysis
DATASET_ID ?= vendor_spend_dataset
TABLE_ID ?= vendor_spend
GCS_BUCKET ?= $(PROJECT_ID)-$(PROJECT_NAME)-contracts
DATA_STORE_ID ?= $(PROJECT_NAME)-datastore

.PHONY: help install-deps generate-pdfs setup-gcs setup-bq setup-vais infra clean

help:
	@echo "Available targets:"
	@echo "  infra           - Run all setup steps (install-deps, setup-gcs, setup-bq, setup-vais)"
	@echo "  setup-gcs       - Create GCS bucket and upload contracts"
	@echo "  setup-bq        - Create BigQuery dataset and load vendor data"
	@echo "  setup-vais      - Create Vertex AI Search datastore and index contracts"
	@echo "  clean         - Remove local generated files"

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
	@echo "Setting up BigQuery dataset: $(DATASET_ID)..."
	uv run python scripts/setup_bigquery.py --project_id $(PROJECT_ID) --dataset_id $(DATASET_ID) --table_id $(TABLE_ID) --region $(REGION)
	@echo "BigQuery setup complete. Dataset: $(PROJECT_ID).$(DATASET_ID).$(TABLE_ID)"

setup-vais:
	@echo "Setting up Vertex AI Search datastore: $(DATA_STORE_ID)..."
	uv run python scripts/setup_vertex_ai_search.py --project_id $(PROJECT_ID) --data_store_id $(DATA_STORE_ID) --gcs_bucket $(GCS_BUCKET) --region $(DATA_STORE_REGION)
	@echo "Vertex AI Search setup complete. Data Store ID: $(DATA_STORE_ID)"

infra: install-deps setup-gcs setup-bq setup-vais
	@echo ""
	@echo "=============================================="
	@echo "Infrastructure setup complete!"
	@echo "=============================================="
	@echo "Project ID:       $(PROJECT_ID)"
	@echo "Region:           $(REGION)"
	@echo "GCS Bucket:       gs://$(GCS_BUCKET)"
	@echo "BigQuery Dataset: $(PROJECT_ID).$(DATASET_ID).$(TABLE_ID)"
	@echo "VAIS Data Store:  $(DATA_STORE_ID)"
	@echo ""
	@echo "Next steps:"
	@echo "1. Configure your ADK agent with these resource IDs"
	@echo "2. Run 'make test' from the project root to test the agent"
	@echo "=============================================="

clean:
	@echo "🧹 Cleaning local generated files..."
	rm -f data/contracts/*.pdf
	rm -f data/structured/*.csv
	@echo "Clean complete."
