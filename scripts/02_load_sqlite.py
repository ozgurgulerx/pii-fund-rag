#!/usr/bin/env python3
"""
Load 250-fund subset into SQLite database.
Creates tables, loads data, and creates indexes.
"""

import csv
import sqlite3
from pathlib import Path

# Paths
SUBSET_DIR = Path("/Users/ozgurguler/Developer/Projects/af-pii-funds/fund-rag-poc/data/subset")
DB_PATH = Path("/Users/ozgurguler/Developer/Projects/af-pii-funds/fund-rag-poc/nport_funds.db")

# Files to load with their table names
FILES_TO_LOAD = [
    "SUBMISSION.tsv",
    "REGISTRANT.tsv",
    "FUND_REPORTED_INFO.tsv",
    "FUND_REPORTED_HOLDING.tsv",
    "IDENTIFIERS.tsv",
    "DEBT_SECURITY.tsv",
    "SECURITIES_LENDING.tsv",
    "MONTHLY_TOTAL_RETURN.tsv",
    "MONTHLY_RETURN_CAT_INSTRUMENT.tsv",
    "INTEREST_RATE_RISK.tsv",
    "EXPLANATORY_NOTE.tsv",
    "DERIVATIVE_COUNTERPARTY.tsv",
    "FWD_FOREIGNCUR_CONTRACT_SWAP.tsv",
    "NONFOREIGN_EXCHANGE_SWAP.tsv",
    "BORROWER.tsv",
]

def load_table(conn, filepath):
    """Load a TSV file into SQLite"""
    table_name = filepath.stem.lower()

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        headers = next(reader)
        headers = [h.lower() for h in headers]

        # Create table
        col_defs = ", ".join([f'"{h}" TEXT' for h in headers])
        conn.execute(f'DROP TABLE IF EXISTS {table_name}')
        conn.execute(f'CREATE TABLE {table_name} ({col_defs})')

        # Insert rows in batches
        placeholders = ", ".join(["?" for _ in headers])
        insert_sql = f'INSERT INTO {table_name} VALUES ({placeholders})'

        batch = []
        count = 0
        for row in reader:
            # Pad row if needed
            while len(row) < len(headers):
                row.append("")
            batch.append(row[:len(headers)])
            count += 1

            if len(batch) >= 10000:
                conn.executemany(insert_sql, batch)
                batch = []

        if batch:
            conn.executemany(insert_sql, batch)

        conn.commit()

    return count

def create_indexes(conn):
    """Create indexes for common queries"""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_holding_accession ON fund_reported_holding(accession_number)",
        "CREATE INDEX IF NOT EXISTS idx_holding_cusip ON fund_reported_holding(issuer_cusip)",
        "CREATE INDEX IF NOT EXISTS idx_holding_asset_cat ON fund_reported_holding(asset_cat)",
        "CREATE INDEX IF NOT EXISTS idx_holding_issuer ON fund_reported_holding(issuer_name)",
        "CREATE INDEX IF NOT EXISTS idx_fund_assets ON fund_reported_info(total_assets)",
        "CREATE INDEX IF NOT EXISTS idx_registrant_name ON registrant(registrant_name)",
        "CREATE INDEX IF NOT EXISTS idx_identifiers_holding ON identifiers(holding_id)",
        "CREATE INDEX IF NOT EXISTS idx_debt_holding ON debt_security(holding_id)",
    ]

    for idx_sql in indexes:
        conn.execute(idx_sql)
    conn.commit()

    return len(indexes)

def create_views(conn):
    """Create useful views"""
    views = [
        # Fund summary view
        """
        CREATE VIEW IF NOT EXISTS fund_summary AS
        SELECT
            f.accession_number,
            f.series_name,
            r.registrant_name,
            CAST(f.total_assets AS REAL) as total_assets,
            CAST(f.net_assets AS REAL) as net_assets,
            COUNT(h.holding_id) as holding_count
        FROM fund_reported_info f
        JOIN registrant r USING (accession_number)
        LEFT JOIN fund_reported_holding h USING (accession_number)
        GROUP BY f.accession_number
        """,
    ]

    for view_sql in views:
        try:
            conn.execute(view_sql)
        except sqlite3.OperationalError:
            pass  # View already exists
    conn.commit()

    return len(views)

def main():
    print("=" * 60)
    print("LOADING DATA INTO SQLITE")
    print("=" * 60)
    print(f"\nDatabase: {DB_PATH}")
    print(f"Source: {SUBSET_DIR}")

    # Remove existing database
    if DB_PATH.exists():
        DB_PATH.unlink()
        print("Removed existing database")

    # Connect to SQLite
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    print("Connected to SQLite")

    # Load data
    print("\nLoading tables...")
    total_rows = 0
    for filename in FILES_TO_LOAD:
        filepath = SUBSET_DIR / filename
        if filepath.exists():
            rows = load_table(conn, filepath)
            total_rows += rows
            print(f"  {filename.lower().replace('.tsv', '')}: {rows:,} rows")
        else:
            print(f"  {filename}: SKIPPED (not found)")

    # Create indexes
    print("\nCreating indexes...")
    num_indexes = create_indexes(conn)
    print(f"  Created {num_indexes} indexes")

    # Create views
    print("\nCreating views...")
    num_views = create_views(conn)
    print(f"  Created {num_views} views")

    # Verify
    print("\nVerifying data...")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM fund_reported_info")
    fund_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM fund_reported_holding")
    holding_count = cur.fetchone()[0]
    cur.execute("SELECT SUM(CAST(total_assets AS REAL)) FROM fund_reported_info")
    total_aum = cur.fetchone()[0]

    print(f"  Funds loaded: {fund_count}")
    print(f"  Holdings loaded: {holding_count:,}")
    print(f"  Total AUM: ${total_aum/1e12:.2f} Trillion")

    # Show sample query
    print("\nSample query - Top 5 funds:")
    cur.execute("""
        SELECT f.series_name, r.registrant_name,
               CAST(f.total_assets AS REAL)/1e9 as assets_b
        FROM fund_reported_info f
        JOIN registrant r USING (accession_number)
        ORDER BY CAST(f.total_assets AS REAL) DESC
        LIMIT 5
    """)
    for row in cur.fetchall():
        print(f"  {row[0][:45]:<45} | {row[1][:25]:<25} | ${row[2]:.1f}B")

    conn.close()

    # Show file size
    size_mb = DB_PATH.stat().st_size / 1e6

    print("\n" + "=" * 60)
    print("SQLITE LOAD COMPLETE")
    print("=" * 60)
    print(f"Total rows loaded: {total_rows:,}")
    print(f"Database size: {size_mb:.1f} MB")
    print(f"Database path: {DB_PATH}")

if __name__ == "__main__":
    main()
