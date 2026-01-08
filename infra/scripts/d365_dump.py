import os
import csv
import re
import json
import base64
import logging
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

# 1. DYNAMICS 365 CREDENTIALS
TENANT_ID = os.getenv("D365_TENANT_ID")
CLIENT_ID = os.getenv("D365_CLIENT_ID")
CLIENT_SECRET = os.getenv("D365_CLIENT_SECRET")
RESOURCE_URL = os.getenv("D365_RESOURCE_URL")

if not all([TENANT_ID, CLIENT_ID, CLIENT_SECRET, RESOURCE_URL]):
    raise ValueError(
        "Missing D365 credentials. Please copy infra/.env.example to infra/.env and fill in your credentials."
    )

# 2. OUTPUT PATHS
BASE_OUTPUT_DIR = Path(__file__).parent.parent / "data"
OUTPUT_CSV_PATH = BASE_OUTPUT_DIR / "structured" / "vendor_spend.csv"
OUTPUT_PDF_DIR = BASE_OUTPUT_DIR / "contracts"

# 3. API CONFIG
API_VERSION = "v9.2"
BASE_URL = f"{RESOURCE_URL}/api/data/{API_VERSION}"
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = [f"{RESOURCE_URL}/.default"]

# 4. LOGGING CONFIG
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# ==================================================================================
# CLASS: DYNAMICS EXTRACTOR
# ==================================================================================

class DynamicsExtractor:
    def __init__(self):
        self.token = self._authenticate()
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Prefer": "odata.include-annotations=\"*\""
        }

    def _authenticate(self):
        """Acquires a bearer token via MSAL."""
        try:
            app = msal.ConfidentialClientApplication(
                CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET
            )
            result = app.acquire_token_for_client(scopes=SCOPE)
            if "access_token" in result:
                return result['access_token']
            else:
                raise Exception(f"Auth Failed: {result.get('error_description')}")
        except Exception as e:
            logger.error(f"Authentication CRITICAL failure: {e}")
            raise

    def fetch_all_accounts(self):
        """Retrieves all accounts with key fields."""
        logger.info("Fetching all accounts from Dynamics 365...")
        query = f"{BASE_URL}/accounts?$select=name,accountid,description"

        response = requests.get(query, headers=self.headers)
        response.raise_for_status()
        if response.status_code == 200:
            accounts = response.json().get('value', [])
            logger.info(f"Found {len(accounts)} accounts.")
            return accounts
        else:
            logger.error(f"Failed to fetch accounts: {response.text}")
            return []

    def fetch_spend_for_account(self, account_id):
        """Sums up all 'Active' or 'New' invoices for a specific account."""
        query = f"{BASE_URL}/invoices?$select=totalamount&$filter=_customerid_value eq '{account_id}'"

        response = requests.get(query, headers=self.headers)
        response.raise_for_status()
        total_spend = 0.0

        if response.status_code == 200:
            invoices = response.json().get('value', [])
            for inv in invoices:
                amount = inv.get('totalamount', 0)
                if amount:
                    total_spend += float(amount)
        
        return total_spend

    def download_all_contract_pdfs(self, account_id, vendor_name):
        """
        Checks for ALL PDF attachments in annotations, downloads them.
        Returns a semicolon-separated string of filenames.
        """
        query = f"{BASE_URL}/annotations?$filter=_objectid_value eq '{account_id}' and isdocument eq true"

        response = requests.get(query, headers=self.headers)
        response.raise_for_status()
        downloaded_files = []

        if response.status_code == 200:
            notes = response.json().get('value', [])
            
            for note in notes:
                note_filename = note.get('filename', 'unknown.pdf')
                
                # Check extension (Case insensitive)
                if note_filename.lower().endswith('.pdf'):
                    body_base64 = note.get('documentbody')
                    if body_base64:
                        try:
                            file_bytes = base64.b64decode(body_base64)
                            
                            # Clean filename
                            safe_name = re.sub(r'[\\/*?:"<>|]', "", note_filename)
                            save_path = OUTPUT_PDF_DIR / safe_name
                            
                            # Handle Duplicate Filenames locally by appending counter if needed
                            # (Optional refinement for very strict systems, but simple overwrite is standard for demos)
                            
                            with open(save_path, 'wb') as f:
                                f.write(file_bytes)
                                
                            logger.info(f"   -> Downloaded Contract: {safe_name}")
                            downloaded_files.append(safe_name)
                            
                        except Exception as e:
                            logger.error(f"   -> Failed to save PDF {note_filename}: {e}")
        
        # Return all found files joined by semicolon
        return ";".join(downloaded_files)

# ==================================================================================
# HELPER FUNCTIONS
# ==================================================================================

def parse_description_metadata(description):
    """Parses 'Vendor ID: X; Renewal Date: YYYY-MM-DD; Status: Active' from string."""
    if not description:
        return None, "2025-01-01", "Active"

    vendor_id_match = re.search(r"Vendor ID:\s*(\d+)", description)
    vendor_id = int(vendor_id_match.group(1)) if vendor_id_match else None

    renewal_match = re.search(r"Renewal Date:\s*(\d{4}-\d{2}-\d{2})", description)
    renewal_date = renewal_match.group(1) if renewal_match else "2025-01-01"

    status_match = re.search(r"Status:\s*(\w+)", description)
    status = status_match.group(1) if status_match else "Active"

    return vendor_id, renewal_date, status

def ensure_directories():
    if not OUTPUT_PDF_DIR.exists():
        OUTPUT_PDF_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {OUTPUT_PDF_DIR}")

    # Ensure structured directory exists for CSV
    csv_dir = OUTPUT_CSV_PATH.parent
    if not csv_dir.exists():
        csv_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {csv_dir}")

# ==================================================================================
# MAIN PIPELINE
# ==================================================================================

def main():
    print("\n--- 🚀 LAUNCHING BATCH EXTRACTION PIPELINE (ETL) [MULTI-FILE SUPPORT] ---")
    
    ensure_directories()
    extractor = DynamicsExtractor()
    
    accounts = extractor.fetch_all_accounts()
    extracted_rows = []
    
    print(f"Processing {len(accounts)} accounts for extraction...")
    
    for acc in accounts:
        name = acc.get('name')
        acc_id = acc.get('accountid')
        description = acc.get('description')

        # A. Structured Data
        spend = extractor.fetch_spend_for_account(acc_id)

        # B. Unstructured Data (Extract ALL PDFs)
        pdf_filenames = extractor.download_all_contract_pdfs(acc_id, name)

        # C. Metadata - Parse vendor_id, renewal_date, status from description
        vendor_id, renewal_date, status = parse_description_metadata(description)

        # Skip accounts without a vendor_id (orphaned PDFs)
        if vendor_id is None:
            logger.warning(f"Skipping {name} - no vendor_id found in description")
            continue

        # D. Determine category based on spend
        if spend >= 100_000_000:
            category = "Strategic"
        elif spend >= 10_000_000:
            category = "Major"
        elif spend >= 1_000_000:
            category = "Standard"
        else:
            category = "Low-Value"

        # E. Build Row
        row = {
            "vendor_id": vendor_id,  # Use original integer vendor_id, not D365 GUID
            "vendor_name": name,
            "total_spend_ytd": int(spend),  # Convert to integer to match BQ schema
            "contract_filename": pdf_filenames, # Now containing "file1.pdf;file2.pdf"
            "renewal_date": renewal_date,
            "status": status,
            "category": category
        }
        extracted_rows.append(row)
        
        if "Apex" in name:
            logger.info(f"*** TRAP DETECTED EXTRACTED *** {name} -> ${spend:,.2f} | Files: {pdf_filenames}")

    # 3. Write to CSV
    logger.info(f"Writing {len(extracted_rows)} records to CSV...")

    with open(OUTPUT_CSV_PATH, mode='w', newline='', encoding='utf-8') as csv_file:
        fieldnames = ["vendor_id", "vendor_name", "total_spend_ytd", "contract_filename", "renewal_date", "status", "category"]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(extracted_rows)
            
    print("\n--- ✅ EXTRACTION COMPLETE ---")
    print(f"1. Structured Data:   {OUTPUT_CSV_PATH}")
    print(f"2. Unstructured Data: {OUTPUT_PDF_DIR}")

if __name__ == "__main__":
    main()