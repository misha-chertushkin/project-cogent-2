import os
import csv
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

CSV_PATH = Path(__file__).parent.parent / "data" / "structured_to_upload" / "vendor_spend.csv"

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

def delete_related_invoices(headers, account_id):
    """Finds and deletes all invoices linked to this Account ID."""
    # Filter for invoices where the customer (account) matches the ID
    query_url = f"{BASE_URL}/invoices?$select=invoiceid&$filter=_customerid_value eq '{account_id}'"

    response = requests.get(query_url, headers=headers)
    response.raise_for_status()

    if response.status_code == 200:
        invoices = response.json().get('value', [])
        for inv in invoices:
            inv_id = inv['invoiceid']
            del_res = requests.delete(f"{BASE_URL}/invoices({inv_id})", headers=headers)
            del_res.raise_for_status()
            if del_res.status_code == 204:
                print(f"   -> [CLEANED] Deleted child invoice: {inv_id}")
            else:
                print(f"   -> [ERROR] Could not delete invoice {inv_id}: {del_res.text}")

def delete_vendor_accounts(headers, vendor_name):
    """Finds ALL accounts with this name, cleans children, and deletes them."""
    safe_name = vendor_name.replace("'", "''")
    query_url = f"{BASE_URL}/accounts?$select=accountid&$filter=name eq '{safe_name}'"

    response = requests.get(query_url, headers=headers)
    response.raise_for_status()

    if response.status_code == 200:
        accounts = response.json().get('value', [])
        
        if not accounts:
            print(f"[SKIP] No accounts found for: {vendor_name}")
            return

        for acc in accounts:
            acc_id = acc['accountid']
            
            # STEP 1: Delete Children (Invoices)
            delete_related_invoices(headers, acc_id)
            
            # STEP 2: Delete Parent (Account)
            del_res = requests.delete(f"{BASE_URL}/accounts({acc_id})", headers=headers)
            del_res.raise_for_status()

            if del_res.status_code == 204:
                print(f"[DELETED] {vendor_name} ({acc_id})")
            else:
                print(f"[ERROR] Could not delete {vendor_name} ({acc_id}): {del_res.text}")
    else:
        print(f"[ERROR] Failed to query {vendor_name}: {response.text}")

# ==================================================================================
# MAIN
# ==================================================================================

def main():
    print("--- STARTING CLEANUP (With Invoice Cascade) ---")
    try:
        token = get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    except Exception as e:
        print(f"Auth Error: {e}")
        return

    if not CSV_PATH.exists():
        print("CSV not found.")
        return

    with open(CSV_PATH, mode='r', encoding='utf-8-sig') as csv_file:
        reader = csv.DictReader(csv_file)
        print("Scanning D365 for vendors to delete...")
        
        for row in reader:
            vendor_name = row.get("vendor_name", "").strip()
            if vendor_name:
                delete_vendor_accounts(headers, vendor_name)

    print("\n--- CLEANUP COMPLETE ---")
    print("1. Verify D365 is empty (search 'Apex Logistics').")
    print("2. Run 'seed_d365.py' EXACTLY ONCE.")

if __name__ == "__main__":
    main()