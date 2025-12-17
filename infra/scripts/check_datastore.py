#!/usr/bin/env python3
"""
Utility script to verify Vertex AI Search datastore exists.

Usage:
    python infra/scripts/check_datastore.py
    python infra/scripts/check_datastore.py --project-id your-project-id
"""

import argparse
import sys
from google.cloud import discoveryengine_v1 as discoveryengine
from google.api_core.client_options import ClientOptions
import google.auth


def check_datastore(project_id: str = None, region: str = "us") -> bool:
    """Check if Vertex AI Search datastore exists.

    Args:
        project_id: GCP project ID. If None, uses default credentials.
        region: Region for the datastore (default: us)

    Returns:
        bool: True if datastore exists, False otherwise
    """
    # Auto-detect project ID if not provided
    if not project_id:
        _, project_id = google.auth.default()

    print(f"Checking Vertex AI Search datastores in project: {project_id}")
    print(f"Region: {region}\n")

    try:
        client_options = ClientOptions(
            api_endpoint=f"{region}-discoveryengine.googleapis.com"
        )
        client = discoveryengine.DataStoreServiceClient(client_options=client_options)

        parent = f"projects/{project_id}/locations/{region}/collections/default_collection"
        datastores = list(client.list_data_stores(parent=parent))

        if not datastores:
            print("❌ No datastores found")
            print("\nRun 'make infra' to create the infrastructure.")
            return False

        print(f"✅ Found {len(datastores)} datastore(s):\n")
        for ds in datastores:
            print(f"  • {ds.display_name}")
            print(f"    ID: {ds.name.split('/')[-1]}")
            print(f"    Full name: {ds.name}\n")

        return True

    except Exception as e:
        print(f"❌ Error checking datastores: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Check Vertex AI Search datastore status"
    )
    parser.add_argument(
        "--project-id",
        help="GCP project ID (defaults to gcloud config or ADC)",
        default=None
    )
    parser.add_argument(
        "--region",
        help="GCP region (default: us)",
        default="us"
    )

    args = parser.parse_args()

    success = check_datastore(project_id=args.project_id, region=args.region)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
