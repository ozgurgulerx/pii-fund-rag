#!/usr/bin/env python3
"""
Migrate N-PORT fund data from SQLite to PostgreSQL
"""

import os
import sqlite3
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Configuration
SQLITE_PATH = os.path.join(os.path.dirname(__file__), '..', 'nport_funds.db')
PG_CONFIG = {
    'host': os.environ.get('PGHOST', 'aistartupstr.postgres.database.azure.com'),
    'port': int(os.environ.get('PGPORT', 5432)),
    'database': 'fundrag',
    'user': os.environ.get('PGUSER', 'ozgurguler'),
    'password': os.environ.get('PGPASSWORD'),
    'sslmode': 'require'
}

BATCH_SIZE = 5000

# Tables to migrate (in order of dependencies)
TABLES = [
    'registrant',
    'submission',
    'fund_reported_info',
    'fund_reported_holding',
    'identifiers',
    'debt_security',
    'interest_rate_risk',
    'monthly_total_return',
    'monthly_return_cat_instrument',
    'derivative_counterparty',
    'fwd_foreigncur_contract_swap',
    'nonforeign_exchange_swap',
    'securities_lending',
    'explanatory_note',
    'borrower'
]


def get_sqlite_schema(cursor, table_name):
    """Get column information from SQLite table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    return [(col[1], col[2]) for col in columns]  # (name, type)


def create_pg_table(pg_cursor, table_name, columns):
    """Create PostgreSQL table with appropriate types"""
    type_mapping = {
        'TEXT': 'TEXT',
        'INTEGER': 'BIGINT',
        'REAL': 'DOUBLE PRECISION',
        'NUMERIC': 'NUMERIC',
        'BLOB': 'BYTEA',
    }

    col_defs = []
    for col_name, col_type in columns:
        pg_type = type_mapping.get(col_type.upper(), 'TEXT')
        col_defs.append(f'"{col_name}" {pg_type}')

    create_sql = f'CREATE TABLE IF NOT EXISTS nport_funds.{table_name} ({", ".join(col_defs)})'
    pg_cursor.execute(create_sql)


def migrate_table(sqlite_cursor, pg_conn, table_name, columns):
    """Migrate a single table from SQLite to PostgreSQL"""
    col_names = [col[0] for col in columns]
    col_names_str = ', '.join([f'"{c}"' for c in col_names])
    placeholders = ', '.join(['%s'] * len(col_names))

    # Count total rows
    sqlite_cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
    total_rows = sqlite_cursor.fetchone()[0]

    if total_rows == 0:
        print(f"  {table_name}: 0 rows (skipped)")
        return 0

    # Fetch and insert in batches
    sqlite_cursor.execute(f'SELECT * FROM {table_name}')

    pg_cursor = pg_conn.cursor()
    rows_migrated = 0

    while True:
        rows = sqlite_cursor.fetchmany(BATCH_SIZE)
        if not rows:
            break

        # Use execute_values for fast bulk insert
        insert_sql = f'INSERT INTO nport_funds.{table_name} ({col_names_str}) VALUES %s'
        execute_values(pg_cursor, insert_sql, rows, page_size=BATCH_SIZE)

        rows_migrated += len(rows)
        print(f"  {table_name}: {rows_migrated}/{total_rows} rows migrated", end='\r')

    pg_conn.commit()
    print(f"  {table_name}: {rows_migrated} rows migrated successfully")
    return rows_migrated


def main():
    print("=" * 60)
    print("N-PORT Fund Data Migration: SQLite → PostgreSQL")
    print("=" * 60)

    # Connect to SQLite
    print(f"\nConnecting to SQLite: {SQLITE_PATH}")
    if not os.path.exists(SQLITE_PATH):
        print(f"ERROR: SQLite database not found at {SQLITE_PATH}")
        return

    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_cursor = sqlite_conn.cursor()

    # Connect to PostgreSQL
    print(f"Connecting to PostgreSQL: {PG_CONFIG['host']}/{PG_CONFIG['database']}")
    try:
        pg_conn = psycopg2.connect(**PG_CONFIG)
        pg_cursor = pg_conn.cursor()
    except Exception as e:
        print(f"ERROR: Could not connect to PostgreSQL: {e}")
        return

    # Create schema
    print("\nCreating schema 'nport_funds'...")
    pg_cursor.execute("CREATE SCHEMA IF NOT EXISTS nport_funds")
    pg_conn.commit()

    # Migrate each table
    print("\nMigrating tables...")
    total_migrated = 0

    for table_name in TABLES:
        # Check if table exists in SQLite
        sqlite_cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        if not sqlite_cursor.fetchone():
            print(f"  {table_name}: not found in SQLite (skipped)")
            continue

        # Get schema
        columns = get_sqlite_schema(sqlite_cursor, table_name)
        if not columns:
            print(f"  {table_name}: no columns (skipped)")
            continue

        # Drop existing table and recreate
        pg_cursor.execute(f"DROP TABLE IF EXISTS nport_funds.{table_name} CASCADE")
        pg_conn.commit()

        # Create table in PostgreSQL
        create_pg_table(pg_cursor, table_name, columns)
        pg_conn.commit()

        # Migrate data
        rows = migrate_table(sqlite_cursor, pg_conn, table_name, columns)
        total_migrated += rows

    # Create indexes for common queries
    print("\nCreating indexes...")
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_holding_accession ON nport_funds.fund_reported_holding(accession_number)",
        "CREATE INDEX IF NOT EXISTS idx_holding_cusip ON nport_funds.fund_reported_holding(issuer_cusip)",
        "CREATE INDEX IF NOT EXISTS idx_holding_asset_cat ON nport_funds.fund_reported_holding(asset_cat)",
        "CREATE INDEX IF NOT EXISTS idx_holding_issuer ON nport_funds.fund_reported_holding(issuer_name)",
        "CREATE INDEX IF NOT EXISTS idx_fund_assets ON nport_funds.fund_reported_info(total_assets)",
        "CREATE INDEX IF NOT EXISTS idx_registrant_name ON nport_funds.registrant(registrant_name)",
        "CREATE INDEX IF NOT EXISTS idx_identifiers_cusip ON nport_funds.identifiers(identifiers_cusip)",
    ]

    for idx_sql in indexes:
        try:
            pg_cursor.execute(idx_sql)
            pg_conn.commit()
            print(f"  Created: {idx_sql.split('idx_')[1].split(' ')[0]}")
        except Exception as e:
            print(f"  Warning: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("Migration Complete!")
    print("=" * 60)
    print(f"Total rows migrated: {total_migrated:,}")

    # Verify counts
    print("\nVerification:")
    for table_name in ['fund_reported_info', 'fund_reported_holding', 'identifiers', 'debt_security']:
        try:
            pg_cursor.execute(f"SELECT COUNT(*) FROM nport_funds.{table_name}")
            count = pg_cursor.fetchone()[0]
            print(f"  {table_name}: {count:,} rows")
        except:
            pass

    # Close connections
    sqlite_conn.close()
    pg_conn.close()

    print("\nDone!")


if __name__ == '__main__':
    main()
