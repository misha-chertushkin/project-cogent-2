#!/usr/bin/env python3
# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Utility script to verify Vertex AI Search datastore exists.

Usage:
    python infra/scripts/check_datastore.py
    python infra/scripts/check_datastore.py --project-id your-project-id
"""

import argparse
import sys
import google.auth
from google.cloud import discoveryengine_v1 as discoveryengine
from google.api_core.client_options import ClientOptions
from google.api_core.exceptions import PermissionDenied, NotFound


def check_datastore(project_id: str = None, datastore_id: str = None, region: str = "us") -> bool:
    """Check if Vertex AI Search datastore exists.

    Args:
        project_id: GCP project ID. If None, uses default credentials.
        datastore_id: Specific identifier of the datastore to verify. If None, lists all available datastores.
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
            api_endpoint=f"{region}-discoveryengine.googleapis.com" if region != "global" else "discoveryengine.googleapis.com"
        )
        client = discoveryengine.DataStoreServiceClient(client_options=client_options)
        parent = f"projects/{project_id}/locations/{region}/collections/default_collection"
        
        datastores = list(client.list_data_stores(parent=parent))
        
        if not datastores:
            print("❌ No datastores found in this project/location.")
            print(f"🔗 Check manually: https://console.cloud.google.com/gen-app-builder/data-stores?project={project_id}")
            return False

        # If a specific ID was requested (e.g., from our Makefile)
        if datastore_id:
            found = any(ds.name.split('/')[-1] == datastore_id for ds in datastores)
            if found:
                print(f"✅ Verified: Datastore '{datastore_id}' is present and active.")
                return True
            else:
                print(f"⚠️  Found other datastores, but '{datastore_id}' is MISSING.")
                return False
            
        # General listing if no specific ID provided
        print(f"✅ Found {len(datastores)} datastore(s):")
        for ds in datastores:
            ds_short_id = ds.name.split('/')[-1]
            print(f"  • {ds.display_name} (ID: {ds_short_id})")
        
        return True

    except PermissionDenied:
        print("❌ Permission Denied. Ensure your account has 'roles/discoveryengine.viewer'.")
        return False
    except Exception as e:
        print(f"❌ Error connecting to Vertex AI Search: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Check Vertex AI Search status")
    parser.add_argument("--project-id", help="GCP Project ID", default=None)
    parser.add_argument("--datastore-id", help="Specific Datastore ID to verify", default=None)
    parser.add_argument("--region", help="GCP region (default: us)", default="us")

    args = parser.parse_args()

    success = check_datastore(
        project_id=args.project_id, 
        datastore_id=args.datastore_id, 
        region=args.region
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
