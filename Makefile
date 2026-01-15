# Makefile for Vendor Spend Analysis Agent
# Streamlined quickstart for the project

# --- Configuration ---
PROJECT_ID ?= $(shell gcloud config get-value project 2>/dev/null)

.PHONY: help install infra demo-e2e playground clean

help:
	@echo "Vendor Spend Analysis Agent - Quick Start"
	@echo ""
	@echo "First, configure your project:"
	@echo "  gcloud config set project <your-project-id>"
	@echo "  gcloud auth application-default set-quota-project <your-project-id>"
	@echo ""
	@echo "Available targets:"
	@echo "  make install     - Install all dependencies (uv + Python packages)"
	@echo "  make infra       - Setup GCP infrastructure (GCS, BigQuery, VAIS)"
	@echo "  make demo-e2e    - End-to-end demo with Dynamics 365 integration"
	@echo "  make playground  - Launch the ADK agent playground"
	@echo "  make clean       - Remove generated files"
	@echo ""
	@echo "Typical workflow:"
	@echo "  1. gcloud config set project <your-project-id>"
	@echo "  2. gcloud auth application-default set-quota-project <your-project-id>"
	@echo "  3. make install"
	@echo "  4. make infra"
	@echo "  5. make playground"

# --- Install Dependencies ---
install:
	@echo "Installing dependencies..."
	@if ! command -v uv &> /dev/null; then \
		echo "Installing uv package manager..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
		export PATH="$$HOME/.local/bin:$$PATH"; \
	fi
	@echo "Syncing Python dependencies..."
	uv sync
	@echo ""
	@echo "Installing infrastructure dependencies..."
	cd infra && uv pip install -r requirements.txt
	@echo ""
	@echo "Dependencies installed successfully!"

# --- Infrastructure Setup ---
infra:
	@if [ -z "$(PROJECT_ID)" ] || [ "$(PROJECT_ID)" = "YOUR-PROJECT-ID" ]; then \
		echo "Error: PROJECT_ID is not set or is placeholder value."; \
		echo "Please run: gcloud config set project YOUR-ACTUAL-PROJECT-ID"; \
		exit 1; \
	fi
	@echo "Setting up infrastructure for project: $(PROJECT_ID)"
	cd infra && $(MAKE) infra

# --- End-to-End Demo ---
demo-e2e:
	@if [ -z "$(PROJECT_ID)" ] || [ "$(PROJECT_ID)" = "YOUR-PROJECT-ID" ]; then \
		echo "Error: PROJECT_ID is not set or is placeholder value."; \
		echo "Please run: gcloud config set project YOUR-ACTUAL-PROJECT-ID"; \
		exit 1; \
	fi
	@echo "Running end-to-end demo for project: $(PROJECT_ID)"
	cd infra && $(MAKE) demo-e2e

# --- Launch Agent Playground ---
playground:
	@echo "Launching ADK Agent Playground..."
	uv run adk web app

# --- Clean Generated Files ---
clean:
	@echo "Cleaning generated files..."
	cd infra && $(MAKE) clean
	@echo "Clean complete."
