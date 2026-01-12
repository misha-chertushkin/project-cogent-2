#!/usr/bin/env python3
"""
Setup Vertex AI Search datastore and import contract documents.

This script creates a Vertex AI Search datastore for unstructured data and
imports PDF contracts from GCS for the hybrid search demo.
"""

import argparse
import sys
import time
import json
from pathlib import Path
from typing import Optional

from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine_v1 as discoveryengine
from google.cloud import resourcemanager_v3

def get_project_number(project_id: str) -> str:
    """Fetch the project number for the given project ID."""
    client = resourcemanager_v3.ProjectsClient()
    project = client.get_project(name=f"projects/{project_id}")
    # The name format is projects/123456789, we split to get '123456789'
    return project.name.split("/")[-1]

def update_metadata_file(project_id: str, project_number: str, data_store_id: str):
    """Update the metadata JSON with current project ID and Number."""
    metadata_path = Path(__file__).parent.parent / "infrastructure_metadata.json"
    
    with open(metadata_path, 'r') as f:
        content = f.read()

    # Replace all placeholders with actual values
    content = content.replace("${PROJECT_ID}", project_id)
    content = content.replace("${PROJECT_NUMBER}", project_number)
    
    with open(metadata_path, 'w') as f:
        f.write(content)
    print(f"✅ Metadata file synchronized for Project: {project_id} (# {project_number})")

def create_data_store(
    project_id: str,
    data_store_id: str,
    region: str,
) -> str:
    """Create Vertex AI Search data store if it doesn't exist."""
    # Initialize client
    client_options = ClientOptions(
        api_endpoint=f"{region}-discoveryengine.googleapis.com"
        if region != "global"
        else "discoveryengine.googleapis.com"
    )
    client = discoveryengine.DataStoreServiceClient(client_options=client_options)

    # Check if data store already exists
    parent = f"projects/{project_id}/locations/{region}/collections/default_collection"
    data_store_path = f"{parent}/dataStores/{data_store_id}"

    try:
        data_store = client.get_data_store(name=data_store_path)
        print(f"Data store {data_store_id} already exists.")
        return data_store.name
    except Exception:
        pass

    # Create data store
    print(f"Creating data store {data_store_id}...")
    data_store = discoveryengine.DataStore(
        display_name=f"{data_store_id}",
        industry_vertical=discoveryengine.IndustryVertical.GENERIC,
        content_config=discoveryengine.DataStore.ContentConfig.CONTENT_REQUIRED,
        solution_types=[discoveryengine.SolutionType.SOLUTION_TYPE_SEARCH],
    )

    request = discoveryengine.CreateDataStoreRequest(
        parent=parent,
        data_store=data_store,
        data_store_id=data_store_id,
    )

    operation = client.create_data_store(request=request)
    print("Waiting for data store creation...")
    response = operation.result(timeout=90)
    print(f"Created data store: {response.name}")

    print("🕒 Sleeping for 60s to allow global propagation (2026 Consistency Check)...")
    time.sleep(60)
    
    return response.name


def import_documents(
    project_id: str,
    data_store_id: str,
    gcs_bucket: str,
    region: str,
) -> None:
    """Import documents from GCS into Vertex AI Search."""
    # Initialize client
    client_options = ClientOptions(
        api_endpoint=f"{region}-discoveryengine.googleapis.com"
        if region != "global"
        else "discoveryengine.googleapis.com"
    )
    client = discoveryengine.DocumentServiceClient(client_options=client_options)

    # Build parent path
    parent = (
        f"projects/{project_id}/locations/{region}/collections/default_collection"
        f"/dataStores/{data_store_id}/branches/default_branch"
    )

    # Configure GCS import
    gcs_source = discoveryengine.GcsSource(
        input_uris=[f"gs://{gcs_bucket}/contracts/*.pdf"],
        data_schema="content",  # Use content schema for PDFs
    )

    request = discoveryengine.ImportDocumentsRequest(
        parent=parent,
        gcs_source=gcs_source,
        reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL,
    )

    print(f"Importing documents from gs://{gcs_bucket}/contracts/...")
    operation = client.import_documents(request=request)

    print("Waiting for import operation to complete...")
    print("(This may take several minutes)")

    # Poll operation status
    while not operation.done():
        time.sleep(10)
        print("  Still importing...")

    try:
        response = operation.result(timeout=600)
        print(f"Import complete!")
        print(f"  Status: {response}")
    except Exception as e:
        print(f"Import failed: {e}")
        sys.exit(1)


def create_search_engine(
    project_id: str,
    data_store_id: str,
    region: str,
) -> Optional[str]:
    """Create a search engine (app) for the data store."""
    try:
        client_options = ClientOptions(
            api_endpoint=f"{region}-discoveryengine.googleapis.com"
            if region != "global"
            else "discoveryengine.googleapis.com"
        )
        client = discoveryengine.EngineServiceClient(client_options=client_options)

        parent = f"projects/{project_id}/locations/{region}/collections/default_collection"
        engine_id = f"{data_store_id}-search"
        engine_path = f"{parent}/engines/{engine_id}"

        # Check if engine exists
        try:
            engine = client.get_engine(name=engine_path)
            print(f"Search engine {engine_id} already exists.")
            return engine.name
        except Exception:
            pass

        # Create engine
        print(f"Creating search engine {engine_id}...")
        engine = discoveryengine.Engine(
            display_name=f"{data_store_id} Search",
            solution_type=discoveryengine.SolutionType.SOLUTION_TYPE_SEARCH,
            data_store_ids=[data_store_id],
            search_engine_config=discoveryengine.Engine.SearchEngineConfig(
                search_tier=discoveryengine.SearchTier.SEARCH_TIER_ENTERPRISE,
            ),
        )

        request = discoveryengine.CreateEngineRequest(
            parent=parent,
            engine=engine,
            engine_id=engine_id,
        )

        operation = client.create_engine(request=request)
        print("Waiting for search engine creation...")
        response = operation.result(timeout=90)
        print(f"Created search engine: {response.name}")
        return response.name
    except Exception as e:
        print(f"Note: Search engine creation optional, skipping: {e}")
        return None


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Setup Vertex AI Search and import contract documents"
    )
    parser.add_argument(
        "--project_id",
        required=True,
        help="GCP Project ID",
    )
    parser.add_argument(
        "--data_store_id",
        required=True,
        help="Vertex AI Search data store ID",
    )
    parser.add_argument(
        "--gcs_bucket",
        required=True,
        help="GCS bucket name containing contracts (without gs:// prefix)",
    )
    parser.add_argument(
        "--region",
        default="us",
        help="Region for Vertex AI Search (default: us, options: us, eu, global)",
    )

    args = parser.parse_args()

    try:
        # 1. Fetch the numeric Project Number (Critical for resource paths)
        print(f"🔍 Fetching project number for {args.project_id}...")
        project_number = get_project_number(
            args.project_id
            )

        # 2. Create data store
        data_store_name = create_data_store(
            args.project_id, 
            args.data_store_id, 
            args.region
            )

        # 3. Import documents
        import_documents(
            args.project_id,
            args.data_store_id,
            args.gcs_bucket,
            args.region,
        )

        update_metadata_file(
            args.project_id, 
            args.data_store_id
            )
        print("\n✅ Vertex AI Search setup and Metadata Sync complete!")

        # 4. Create search engine (optional)
        create_search_engine(
            args.project_id,
            args.data_store_id,
            args.region,
        )

        # 5. SYNC METADATA - Replaces project ID and NUMBER in JSON
        update_metadata_file(
            args.project_id, 
            project_number, 
            args.data_store_id
            )

        print("\n" + "=" * 50)
        print("Vertex AI Search setup complete!")
        print("=" * 50)
        print(f"Project ID:    {args.project_id}")
        print(f"Project Num:   {project_number}")
        print(f"Data Store ID: {args.data_store_id}")
        print(f"Region:        {args.region}")
        print(f"GCS Source:    gs://{args.gcs_bucket}/contracts/")
        print(f"Documents:     20 PDF contracts")
        print("\nTrap document: Apex_Logistics_MSA.pdf")
        print("  - Contains: Termination Date = 2024-12-31 (EXPIRED!)")
        print("  - Look for: Section 2 (TERM AND TERMINATION)")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
