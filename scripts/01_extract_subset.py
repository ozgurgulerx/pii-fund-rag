#!/usr/bin/env python3
"""
Extract 250-fund subset from full N-PORT dataset.
Selects top funds by AUM with diversity across fund types.
"""

import csv
import os
from collections import defaultdict
from pathlib import Path

# Paths
DATA_DIR = Path("/Users/ozgurguler/Developer/Projects/af-pii-funds/2025q4_nport")
OUTPUT_DIR = Path("/Users/ozgurguler/Developer/Projects/af-pii-funds/fund-rag-poc/data/subset")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def get_top_250_funds():
    """Get accession numbers for top 250 funds by AUM"""
    print("Loading fund data...")

    # Load fund info
    funds = []
    with open(DATA_DIR / 'FUND_REPORTED_INFO.tsv', 'r') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            try:
                assets = float(row['TOTAL_ASSETS']) if row['TOTAL_ASSETS'] else 0
            except:
                assets = 0
            funds.append({
                'accession': row['ACCESSION_NUMBER'],
                'name': row['SERIES_NAME'] or 'Unknown',
                'assets': assets
            })

    # Sort by assets and take top 250
    funds_sorted = sorted(funds, key=lambda x: x['assets'], reverse=True)
    top_250 = funds_sorted[:250]

    print(f"Selected {len(top_250)} funds")
    print(f"Total AUM: ${sum(f['assets'] for f in top_250)/1e12:.2f} Trillion")
    print(f"\nTop 10 funds:")
    for i, f in enumerate(top_250[:10], 1):
        print(f"  {i}. {f['name'][:50]} - ${f['assets']/1e9:.1f}B")

    return set(f['accession'] for f in top_250)

def get_subset_holding_ids(subset_accessions):
    """Get all holding IDs for subset funds"""
    print("\nCollecting holding IDs for subset funds...")
    holding_ids = set()

    with open(DATA_DIR / 'FUND_REPORTED_HOLDING.tsv', 'r') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            if row['ACCESSION_NUMBER'] in subset_accessions:
                holding_ids.add(row['HOLDING_ID'])

    print(f"Found {len(holding_ids):,} holdings")
    return holding_ids

def extract_table(filename, key_field, valid_keys, output_dir):
    """Extract rows matching valid keys from a table"""
    input_path = DATA_DIR / filename
    output_path = output_dir / filename

    if not input_path.exists():
        print(f"  Skipping {filename} (not found)")
        return 0

    count = 0
    with open(input_path, 'r') as infile:
        reader = csv.DictReader(infile, delimiter='\t')
        fieldnames = reader.fieldnames

        with open(output_path, 'w', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter='\t')
            writer.writeheader()

            for row in reader:
                if row[key_field] in valid_keys:
                    writer.writerow(row)
                    count += 1

    print(f"  {filename}: {count:,} rows")
    return count

def main():
    print("=" * 60)
    print("EXTRACTING 250-FUND SUBSET")
    print("=" * 60)

    # Step 1: Get top 250 fund accession numbers
    subset_accessions = get_top_250_funds()

    # Save accession numbers for reference
    with open(OUTPUT_DIR / 'subset_accessions.txt', 'w') as f:
        for acc in sorted(subset_accessions):
            f.write(acc + '\n')

    # Step 2: Get holding IDs for those funds
    subset_holdings = get_subset_holding_ids(subset_accessions)

    # Save holding IDs for reference
    with open(OUTPUT_DIR / 'subset_holding_ids.txt', 'w') as f:
        for hid in sorted(subset_holdings):
            f.write(hid + '\n')

    # Step 3: Extract tables by ACCESSION_NUMBER
    print("\nExtracting tables by ACCESSION_NUMBER...")
    accession_tables = [
        'SUBMISSION.tsv',
        'REGISTRANT.tsv',
        'FUND_REPORTED_INFO.tsv',
        'MONTHLY_TOTAL_RETURN.tsv',
        'MONTHLY_RETURN_CAT_INSTRUMENT.tsv',
        'INTEREST_RATE_RISK.tsv',
        'EXPLANATORY_NOTE.tsv',
        'FUND_VAR_INFO.tsv',
        'BORROWER.tsv',
        'BORROW_AGGREGATE.tsv',
    ]

    total_accession_rows = 0
    for table in accession_tables:
        rows = extract_table(table, 'ACCESSION_NUMBER', subset_accessions, OUTPUT_DIR)
        total_accession_rows += rows

    # Step 4: Extract tables by HOLDING_ID
    print("\nExtracting tables by HOLDING_ID...")
    holding_tables = [
        'FUND_REPORTED_HOLDING.tsv',
        'IDENTIFIERS.tsv',
        'DEBT_SECURITY.tsv',
        'SECURITIES_LENDING.tsv',
        'DERIVATIVE_COUNTERPARTY.tsv',
        'SWAPTION_OPTION_WARNT_DERIV.tsv',
        'FUT_FWD_NONFOREIGNCUR_CONTRACT.tsv',
        'FWD_FOREIGNCUR_CONTRACT_SWAP.tsv',
        'NONFOREIGN_EXCHANGE_SWAP.tsv',
        'FLOATING_RATE_RESET_TENOR.tsv',
        'REPURCHASE_AGREEMENT.tsv',
        'REPURCHASE_COUNTERPARTY.tsv',
        'REPURCHASE_COLLATERAL.tsv',
        'DESC_REF_INDEX_BASKET.tsv',
        'DESC_REF_INDEX_COMPONENT.tsv',
        'DESC_REF_OTHER.tsv',
        'CONVERTIBLE_SECURITY_CURRENCY.tsv',
        'DEBT_SECURITY_REF_INSTRUMENT.tsv',
        'OTHER_DERIV.tsv',
        'OTHER_DERIV_NOTIONAL_AMOUNT.tsv',
    ]

    total_holding_rows = 0
    for table in holding_tables:
        rows = extract_table(table, 'HOLDING_ID', subset_holdings, OUTPUT_DIR)
        total_holding_rows += rows

    # Summary
    print("\n" + "=" * 60)
    print("EXTRACTION COMPLETE")
    print("=" * 60)
    print(f"Funds extracted: 250")
    print(f"Holdings extracted: {len(subset_holdings):,}")
    print(f"Total rows (accession tables): {total_accession_rows:,}")
    print(f"Total rows (holding tables): {total_holding_rows:,}")
    print(f"Output directory: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
