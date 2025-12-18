"""Configuration management for the Vendor Spend Analysis Agent.

This module provides centralized configuration with sensible defaults.
Environment variables can override defaults if needed.
"""

import os
import google.auth

# GCP Configuration - auto-detect project ID from credentials
_, PROJECT_ID = google.auth.default()
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", PROJECT_ID)
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

# Model Configuration
# Using gemini-2.0-flash-exp for better performance while still being available
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-3-pro-preview")

# BigQuery Configuration
BQ_DATASET_ID = os.getenv("BQ_DATASET_ID", "vendor_spend_dataset")
BQ_TABLE_ID = os.getenv("BQ_TABLE_ID", "vendor_spend")
BQ_LOCATION = os.getenv("BQ_LOCATION", "us-central1")
DATA_STORE_ID = os.getenv("DATA_STORE_ID", "vendor-analysis-datastore")

# Vertex AI Search Configuration
DATA_STORE_REGION = os.getenv("DATA_STORE_REGION", "us")
# Full resource name for Vertex AI Search datastore
VERTEX_AI_SEARCH_DATASTORE = os.getenv(
    "VERTEX_AI_SEARCH_DATASTORE",
    f"projects/{PROJECT_ID}/locations/{DATA_STORE_REGION}/collections/default_collection/dataStores/{DATA_STORE_ID}"
)
