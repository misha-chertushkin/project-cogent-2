import os
import csv
import re
import json
import base64
import requests
import msal
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# ==================================================================================
# CONFIGURATION
# ==================================================================================
TENANT_ID = os.getenv("D365_TENANT_ID")
CLIENT_ID = os.getenv("D365_CLIENT_ID")
CLIENT_SECRET = os.getenv("D365_CLIENT_SECRET")
RESOURCE_URL = os.getenv("D365_RESOURCE_URL")

if not all([TENANT_ID, CLIENT_ID, CLIENT_SECRET, RESOURCE_URL]):
    raise ValueError(
        "Missing D365 credentials. Please copy infra/.env.example to infra/.env and fill in your credentials."
    )

# PATHS
CSV_PATH = "/home/chertushkin/project-cogent-2/infra/data/structured_to_upload/vendor_spend.csv"
PDF_DIR = "/home/chertushkin/project-cogent-2/infra/data/contracts_to_upload"

# API
API_VERSION = "v9.2"
BASE_URL = f"{RESOURCE_URL}/api/data/{API_VERSION}"
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = [f"{RESOURCE_URL}/.default"]

# ==================================================================================
# HELPER FUNCTIONS
# ==================================================================================

def get_access_token():
    app = msal.ConfidentialClientApplication(
        CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET
    )
    result = app.acquire_token_for_client(scopes=SCOPE)
    if "access_token" in result:
        return result['access_token']
    else:
        raise Exception(f"Auth Failed: {result.get('error_description')}")

def clean_currency(value_str):
    if not value_str: return 0.0
    clean = value_str.replace('$', '').replace(',', '').strip()
    return float(clean)

def infer_vendor_name_from_file(filename):
    """
    Intelligently guesses Vendor Name from filename.
    Ex: '{trap}Apex_Logistics_MSA.pdf' -> 'Apex Logistics'
    Ex: 'CloudNine_Hosting_MSA.pdf' -> 'CloudNine Hosting'
    """
    name = filename.replace(".pdf", "")
    name = name.replace("{trap}", "")
    name = re.sub(r"_MSA$", "", name, flags=re.IGNORECASE)
    name = re.sub(r"_Contract.*", "", name, flags=re.IGNORECASE)
    name = name.replace("_", " ")
    return name.strip()

# ==================================================================================
# D365 ACTIONS
# ==================================================================================

def create_account(headers, name, description="Created by Master Seed"):
    """Creates account and returns ID."""
    payload = {"name": name, "description": description}
    res = requests.post(f"{BASE_URL}/accounts", headers=headers, json=payload)
    
    if res.status_code == 204:
        entity_url = res.headers.get("OData-EntityId")
        return entity_url.split("(")[1].split(")")[0]
    return None

def create_invoice(headers, account_id, amount):
    """Creates invoice linked to account."""
    if amount <= 0: return
    payload = {
        "name": "Consolidated Annual Spend",
        "totalamount": amount,
        "customerid_account@odata.bind": f"/accounts({account_id})"
    }
    requests.post(f"{BASE_URL}/invoices", headers=headers, json=payload)

def upload_pdf(headers, account_id, filename):
    """Uploads PDF from local folder to account."""
    full_path = os.path.join(PDF_DIR, filename)
    if not os.path.exists(full_path):
        print(f"   [WARNING] File missing locally: {filename}")
        return

    with open(full_path, "rb") as f:
        encoded_string = base64.b64encode(f.read()).decode('utf-8')

    payload = {
        "subject": "Vendor Agreement",
        "notetext": f"Auto-uploaded: {filename}",
        "filename": filename,
        "documentbody": encoded_string,
        "mimetype": "application/pdf",
        "objectid_account@odata.bind": f"/accounts({account_id})"
    }
    requests.post(f"{BASE_URL}/annotations", headers=headers, json=payload)

# ==================================================================================
# MAIN LOGIC
# ==================================================================================

def main():
    print("--- 🚀 STARTING MASTER D365 BACKFILL ---")
    
    # 1. Auth
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Dictionary to track created accounts: { "Vendor Name": "GUID" }
    vendor_map = {} 

    # --------------------------------------------------------------------------
    # PHASE 1: PROCESS STRUCTURED DATA (CSV)
    # --------------------------------------------------------------------------
    print("\n[PHASE 1] Seeding Accounts & Invoices from CSV...")
    
    with open(CSV_PATH, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            vendor_id = row.get("vendor_id", "").strip()
            vendor_name = row.get("vendor_name", "").strip()
            spend = clean_currency(row.get("total_spend_ytd", "0"))
            renewal = row.get("renewal_date", "")
            status = row.get("status", "Active")

            # Trap Metadata stored in description - INCLUDE ORIGINAL VENDOR_ID
            desc = f"Vendor ID: {vendor_id}; Renewal Date: {renewal}; Status: {status}; Type: Vendor"

            # Create Account
            acct_id = create_account(headers, vendor_name, desc)
            
            if acct_id:
                print(f"   + Created: {vendor_name}")
                vendor_map[vendor_name] = acct_id # Save to map
                
                # Create Invoice
                create_invoice(headers, acct_id, spend)
    
    # --------------------------------------------------------------------------
    # PHASE 2: PROCESS UNSTRUCTURED DATA (ALL FILES)
    # --------------------------------------------------------------------------
    print("\n[PHASE 2] Uploading ALL PDFs from Folder...")
    
    if os.path.exists(PDF_DIR):
        files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")]
        
        for filename in sorted(files):
            # Infer name (e.g. "Apex_Logistics_MSA.pdf" -> "Apex Logistics")
            inferred_name = infer_vendor_name_from_file(filename)
            
            # CHECK: Do we already have this account from Phase 1?
            target_id = vendor_map.get(inferred_name)
            
            if target_id:
                # Yes -> Just upload the file to existing account
                print(f"   > Uploading {filename} -> Existing '{inferred_name}'")
                upload_pdf(headers, target_id, filename)
            else:
                # No -> This is an "Orphan" PDF (not in CSV). Create new Account.
                print(f"   > New Vendor Found: '{inferred_name}' -> Creating & Uploading...")
                new_id = create_account(headers, inferred_name, "Created from PDF Scan")
                if new_id:
                    vendor_map[inferred_name] = new_id # Update map
                    upload_pdf(headers, new_id, filename)
    else:
        print(f"[ERROR] PDF Directory not found: {PDF_DIR}")

    print("\n--- ✅ MASTER SETUP COMPLETE ---")
    print(f"Total Unique Vendors in D365: {len(vendor_map)}")

if __name__ == "__main__":
    main()