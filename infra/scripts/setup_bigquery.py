#!/usr/bin/env python3
"""
Setup BigQuery dataset and load vendor spend data.

This script creates a BigQuery dataset and table, then loads the vendor spend
CSV data for the hybrid search demo.
"""

import argparse
import sys
from pathlib import Path

from google.cloud import bigquery
from google.cloud.exceptions import NotFound


def create_dataset(client: bigquery.Client, dataset_id: str, region: str) -> bigquery.Dataset:
    """Create BigQuery dataset if it doesn't exist."""
    dataset_ref = f"{client.project}.{dataset_id}"

    try:
        dataset = client.get_dataset(dataset_ref)
        print(f"Dataset {dataset_ref} already exists.")
        return dataset
    except NotFound:
        print(f"Creating dataset {dataset_ref}...")
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = region
        dataset = client.create_dataset(dataset, timeout=30)
        print(f"Created dataset {dataset_ref}")
        return dataset


def create_table_schema() -> list:
    """Define the schema for the vendor spend table."""
    return [
        bigquery.SchemaField("vendor_id", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("vendor_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("total_spend_ytd", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("contract_filename", "STRING", mode="NULLABLE"),  # Some vendors may not have contracts
        bigquery.SchemaField("renewal_date", "DATE", mode="REQUIRED"),
        bigquery.SchemaField("status", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("category", "STRING", mode="REQUIRED"),
    ]


def load_csv_to_table(
    client: bigquery.Client,
    dataset_id: str,
    table_id: str,
    csv_path: Path,
) -> None:
    """Load CSV data into BigQuery table."""
    table_ref = f"{client.project}.{dataset_id}.{table_id}"

    # Define table schema
    schema = create_table_schema()

    # Create or replace table
    table = bigquery.Table(table_ref, schema=schema)
    try:
        client.delete_table(table_ref)
        print(f"Deleted existing table {table_ref}")
    except NotFound:
        pass

    table = client.create_table(table)
    print(f"Created table {table_ref}")

    # Load CSV data
    job_config = bigquery.LoadJobConfig(
    schema=schema,
    skip_leading_rows=1,
    source_format=bigquery.SourceFormat.CSV,
    write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    allow_quoted_newlines=True,
    # This is the magic line for 2026:
    autodetect=False,
    )

    with open(csv_path, "rb") as source_file:
        load_job = client.load_table_from_file(
            source_file,
            table_ref,
            job_config=job_config,
        )

    print(f"Loading data from {csv_path}...")
    load_job.result()  # Wait for the job to complete

    # Verify load
    table = client.get_table(table_ref)
    print(f"Loaded {table.num_rows} rows into {table_ref}")

    # Display sample data
    query = f"""
    SELECT vendor_id, vendor_name, total_spend_ytd, renewal_date, status
    FROM `{table_ref}`
    WHERE total_spend_ytd > 100000000
    ORDER BY total_spend_ytd DESC
    LIMIT 10
    """
    print("\nSample high-value vendors (>$100M):")
    query_job = client.query(query)
    for row in query_job:
        print(f"  ID {row.vendor_id}: {row.vendor_name} - ${row.total_spend_ytd:,} (Renews: {row.renewal_date}, Status: {row.status})")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Setup BigQuery dataset and load vendor spend data"
    )
    parser.add_argument(
        "--project_id",
        required=True,
        help="GCP Project ID",
    )
    parser.add_argument(
        "--dataset_id",
        default="vendor_spend_dataset",
        help="BigQuery dataset ID (default: vendor_spend_dataset)",
    )
    parser.add_argument(
        "--table_id",
        default="vendor_spend",
        help="BigQuery table ID (default: vendor_spend)",
    )
    parser.add_argument(
        "--region",
        default="us-central1",
        help="GCP region (default: us-central1)",
    )

    args = parser.parse_args()

    # Locate CSV file
    script_dir = Path(__file__).parent
    csv_path = script_dir.parent / "data" / "structured" / "vendor_spend.csv"

    if not csv_path.exists():
        print(f"Error: CSV file not found at {csv_path}")
        print("Please run 'make generate-pdfs' first to create the data files.")
        sys.exit(1)

    # Initialize BigQuery client
    client = bigquery.Client(project=args.project_id)

    try:
        # Create dataset
        create_dataset(client, args.dataset_id, args.region)

        # Load data into table
        load_csv_to_table(
            client,
            args.dataset_id,
            args.table_id,
            csv_path,
        )

        print("\n" + "=" * 50)
        print("BigQuery setup complete!")
        print("=" * 50)
        print(f"Dataset: {args.project_id}.{args.dataset_id}")
        print(f"Table:   {args.project_id}.{args.dataset_id}.{args.table_id}")
        print(f"Rows:    50 vendors (6 with spend >$100M)")
        print("\nTrap record: Vendor ID 99 (Apex Logistics)")
        print("  - Database shows: Status=Active, Renewal=2027-01-01")
        print("  - Contract PDF shows: Terminates 2024-12-31 (EXPIRED!)")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
