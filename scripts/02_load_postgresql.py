#!/usr/bin/env python3
"""
Load 250-fund subset into Azure PostgreSQL.
Creates schema, tables, loads data, and creates indexes.
"""

import csv
import os
from pathlib import Path
from dotenv import load_dotenv

# Try to import psycopg2, fall back to psycopg if not available
try:
    import psycopg2
    from psycopg2 import sql
    from psycopg2.extras import execute_values
    PG_MODULE = "psycopg2"
except ImportError:
    try:
        import psycopg
        PG_MODULE = "psycopg"
    except ImportError:
        print("ERROR: Neither psycopg2 nor psycopg is installed.")
        print("Install with: pip install psycopg2-binary")
        exit(1)

# Load environment variables
load_dotenv("/Users/ozgurguler/Developer/Projects/af-pii-funds/.env")

# Paths
SUBSET_DIR = Path("/Users/ozgurguler/Developer/Projects/af-pii-funds/fund-rag-poc/data/subset")

# PostgreSQL connection
DB_CONFIG = {
    "host": os.getenv("PGHOST"),
    "database": os.getenv("PGDATABASE"),
    "user": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD"),
    "port": os.getenv("PGPORT", "5432"),
    "sslmode": "require"
}

SCHEMA_NAME = "nport_funds"

# Table definitions with proper data types
TABLE_SCHEMAS = {
    "submission": """
        accession_number VARCHAR(30) PRIMARY KEY,
        filing_date DATE,
        file_num VARCHAR(20),
        sub_type VARCHAR(20),
        report_ending_period DATE,
        report_date DATE,
        is_last_filing VARCHAR(5)
    """,
    "registrant": """
        accession_number VARCHAR(30) PRIMARY KEY,
        cik VARCHAR(15),
        registrant_name VARCHAR(300),
        file_num VARCHAR(20),
        lei VARCHAR(25),
        address1 VARCHAR(200),
        address2 VARCHAR(200),
        city VARCHAR(100),
        state VARCHAR(20),
        country VARCHAR(10),
        zip VARCHAR(20),
        phone VARCHAR(30)
    """,
    "fund_reported_info": """
        accession_number VARCHAR(30) PRIMARY KEY,
        series_name VARCHAR(300),
        series_id VARCHAR(20),
        series_lei VARCHAR(25),
        total_assets NUMERIC(25,2),
        total_liabilities NUMERIC(25,2),
        net_assets NUMERIC(25,2),
        assets_attrbt_to_misc_security NUMERIC(25,2),
        assets_invested NUMERIC(25,2),
        borrowing_pay_within_1yr NUMERIC(25,2),
        ctrld_companies_pay_within_1yr NUMERIC(25,2),
        other_affilia_pay_within_1yr NUMERIC(25,2),
        other_pay_within_1yr NUMERIC(25,2),
        borrowing_pay_after_1yr NUMERIC(25,2),
        ctrld_companies_pay_after_1yr NUMERIC(25,2),
        other_affilia_pay_after_1yr NUMERIC(25,2),
        other_pay_after_1yr NUMERIC(25,2),
        delayed_delivery NUMERIC(25,2),
        standby_commitment NUMERIC(25,2),
        liquidation_preference NUMERIC(25,2),
        cash_not_rptd_in_c_or_d NUMERIC(25,2),
        credit_spread_3mon_invest NUMERIC(25,6),
        credit_spread_1yr_invest NUMERIC(25,6),
        credit_spread_5yr_invest NUMERIC(25,6),
        credit_spread_10yr_invest NUMERIC(25,6),
        credit_spread_30yr_invest NUMERIC(25,6),
        credit_spread_3mon_noninvest NUMERIC(25,6),
        credit_spread_1yr_noninvest NUMERIC(25,6),
        credit_spread_5yr_noninvest NUMERIC(25,6),
        credit_spread_10yr_noninvest NUMERIC(25,6),
        credit_spread_30yr_noninvest NUMERIC(25,6),
        is_non_cash_collateral VARCHAR(5),
        net_realize_gain_nonderiv_mon1 NUMERIC(25,2),
        net_unrealize_ap_nonderiv_mon1 NUMERIC(25,2),
        net_realize_gain_nonderiv_mon2 NUMERIC(25,2),
        net_unrealize_ap_nonderiv_mon2 NUMERIC(25,2),
        net_realize_gain_nonderiv_mon3 NUMERIC(25,2),
        net_unrealize_ap_nonderiv_mon3 NUMERIC(25,2),
        sales_flow_mon1 NUMERIC(25,2),
        reinvestment_flow_mon1 NUMERIC(25,2),
        redemption_flow_mon1 NUMERIC(25,2),
        sales_flow_mon2 NUMERIC(25,2),
        reinvestment_flow_mon2 NUMERIC(25,2),
        redemption_flow_mon2 NUMERIC(25,2),
        sales_flow_mon3 NUMERIC(25,2),
        reinvestment_flow_mon3 NUMERIC(25,2),
        redemption_flow_mon3 NUMERIC(25,2)
    """,
    "fund_reported_holding": """
        accession_number VARCHAR(30),
        holding_id VARCHAR(25),
        issuer_name VARCHAR(300),
        issuer_lei VARCHAR(25),
        issuer_title VARCHAR(500),
        issuer_cusip VARCHAR(15),
        balance NUMERIC(25,6),
        unit VARCHAR(20),
        other_unit_desc VARCHAR(100),
        currency_code VARCHAR(10),
        currency_value NUMERIC(25,4),
        exchange_rate NUMERIC(20,10),
        percentage NUMERIC(15,10),
        payoff_profile VARCHAR(20),
        asset_cat VARCHAR(20),
        other_asset VARCHAR(100),
        issuer_type VARCHAR(20),
        other_issuer VARCHAR(100),
        investment_country VARCHAR(10),
        is_restricted_security VARCHAR(5),
        fair_value_level VARCHAR(5),
        derivative_cat VARCHAR(20),
        PRIMARY KEY (accession_number, holding_id)
    """,
    "identifiers": """
        holding_id VARCHAR(25),
        identifiers_id VARCHAR(25),
        identifier_isin VARCHAR(20),
        identifier_ticker VARCHAR(30),
        other_identifier VARCHAR(50),
        other_identifier_desc VARCHAR(100),
        PRIMARY KEY (holding_id, identifiers_id)
    """,
    "debt_security": """
        holding_id VARCHAR(25) PRIMARY KEY,
        maturity_date VARCHAR(20),
        coupon_type VARCHAR(20),
        annualized_rate NUMERIC(15,8),
        is_default VARCHAR(5),
        are_any_interest_payment VARCHAR(5),
        is_any_portion_interest_paid VARCHAR(5),
        is_convtible_mandatory VARCHAR(5),
        is_convtible_contingent VARCHAR(5)
    """,
    "securities_lending": """
        holding_id VARCHAR(25) PRIMARY KEY,
        is_cash_collateral VARCHAR(5),
        cash_collateral_amount NUMERIC(25,4),
        is_non_cash_collateral VARCHAR(5),
        non_cash_collateral_value NUMERIC(25,4),
        is_loan_by_fund VARCHAR(5),
        loan_value NUMERIC(25,4)
    """,
    "monthly_total_return": """
        accession_number VARCHAR(30),
        monthly_total_return_id VARCHAR(25),
        class_id VARCHAR(20),
        monthly_total_return1 NUMERIC(15,8),
        monthly_total_return2 NUMERIC(15,8),
        monthly_total_return3 NUMERIC(15,8),
        PRIMARY KEY (accession_number, monthly_total_return_id)
    """,
    "interest_rate_risk": """
        accession_number VARCHAR(30),
        interest_rate_risk_id VARCHAR(25),
        currency_code VARCHAR(10),
        intrst_rate_change_3mon_dv01 NUMERIC(25,6),
        intrst_rate_change_1yr_dv01 NUMERIC(25,6),
        intrst_rate_change_5yr_dv01 NUMERIC(25,6),
        intrst_rate_change_10yr_dv01 NUMERIC(25,6),
        intrst_rate_change_30yr_dv01 NUMERIC(25,6),
        intrst_rate_change_3mon_dv100 NUMERIC(25,6),
        intrst_rate_change_1yr_dv100 NUMERIC(25,6),
        intrst_rate_change_5yr_dv100 NUMERIC(25,6),
        intrst_rate_change_10yr_dv100 NUMERIC(25,6),
        intrst_rate_change_30yr_dv100 NUMERIC(25,6),
        PRIMARY KEY (accession_number, interest_rate_risk_id)
    """,
    "explanatory_note": """
        accession_number VARCHAR(30),
        explanatory_note_id VARCHAR(25),
        item_no VARCHAR(20),
        explanatory_note TEXT,
        PRIMARY KEY (accession_number, explanatory_note_id)
    """,
    "derivative_counterparty": """
        holding_id VARCHAR(25),
        derivative_counterparty_id VARCHAR(25),
        derivative_counterparty_name VARCHAR(300),
        derivative_counterparty_lei VARCHAR(25),
        PRIMARY KEY (holding_id, derivative_counterparty_id)
    """,
    "borrower": """
        accession_number VARCHAR(30),
        borrower_id VARCHAR(25),
        name VARCHAR(300),
        lei VARCHAR(25),
        aggregate_value NUMERIC(25,4),
        PRIMARY KEY (accession_number, borrower_id)
    """
}

# Files to load (in order)
FILES_TO_LOAD = [
    ("SUBMISSION.tsv", "submission"),
    ("REGISTRANT.tsv", "registrant"),
    ("FUND_REPORTED_INFO.tsv", "fund_reported_info"),
    ("FUND_REPORTED_HOLDING.tsv", "fund_reported_holding"),
    ("IDENTIFIERS.tsv", "identifiers"),
    ("DEBT_SECURITY.tsv", "debt_security"),
    ("SECURITIES_LENDING.tsv", "securities_lending"),
    ("MONTHLY_TOTAL_RETURN.tsv", "monthly_total_return"),
    ("INTEREST_RATE_RISK.tsv", "interest_rate_risk"),
    ("EXPLANATORY_NOTE.tsv", "explanatory_note"),
    ("DERIVATIVE_COUNTERPARTY.tsv", "derivative_counterparty"),
    ("BORROWER.tsv", "borrower"),
]

def get_connection():
    """Get PostgreSQL connection"""
    if PG_MODULE == "psycopg2":
        return psycopg2.connect(**DB_CONFIG)
    else:
        conn_str = f"host={DB_CONFIG['host']} dbname={DB_CONFIG['database']} user={DB_CONFIG['user']} password={DB_CONFIG['password']} port={DB_CONFIG['port']} sslmode=require"
        return psycopg.connect(conn_str)

def create_schema(conn):
    """Create the nport_funds schema"""
    with conn.cursor() as cur:
        cur.execute(f"DROP SCHEMA IF EXISTS {SCHEMA_NAME} CASCADE")
        cur.execute(f"CREATE SCHEMA {SCHEMA_NAME}")
        conn.commit()
    print(f"Created schema: {SCHEMA_NAME}")

def create_tables(conn):
    """Create all tables"""
    with conn.cursor() as cur:
        for table_name, schema in TABLE_SCHEMAS.items():
            cur.execute(f"DROP TABLE IF EXISTS {SCHEMA_NAME}.{table_name} CASCADE")
            cur.execute(f"CREATE TABLE {SCHEMA_NAME}.{table_name} ({schema})")
        conn.commit()
    print(f"Created {len(TABLE_SCHEMAS)} tables")

def clean_value(value, target_type="text"):
    """Clean and convert value for PostgreSQL"""
    if value is None or value == "" or value.strip() == "":
        return None
    value = value.strip()
    if target_type == "numeric":
        try:
            return float(value)
        except:
            return None
    return value

def load_table(conn, filename, table_name):
    """Load a TSV file into a table"""
    filepath = SUBSET_DIR / filename
    if not filepath.exists():
        print(f"  Skipping {filename} (not found)")
        return 0

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        columns = [c.lower() for c in reader.fieldnames]

        # Get table columns that exist in the schema
        schema_cols = TABLE_SCHEMAS.get(table_name, "")
        available_cols = [c.strip().split()[0] for c in schema_cols.split(',') if c.strip()]

        # Filter to columns that exist in both file and schema
        cols_to_use = [c for c in columns if c in available_cols]

        rows = []
        for row in reader:
            values = []
            for col in cols_to_use:
                orig_col = [c for c in reader.fieldnames if c.lower() == col][0]
                values.append(clean_value(row[orig_col]))
            rows.append(tuple(values))

        if not rows:
            return 0

        # Build INSERT statement
        col_names = ", ".join(cols_to_use)
        placeholders = ", ".join(["%s"] * len(cols_to_use))
        insert_sql = f"INSERT INTO {SCHEMA_NAME}.{table_name} ({col_names}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"

        # Batch insert
        with conn.cursor() as cur:
            batch_size = 10000
            for i in range(0, len(rows), batch_size):
                batch = rows[i:i + batch_size]
                cur.executemany(insert_sql, batch)
            conn.commit()

    return len(rows)

def create_indexes(conn):
    """Create indexes for common queries"""
    indexes = [
        f"CREATE INDEX idx_holding_accession ON {SCHEMA_NAME}.fund_reported_holding(accession_number)",
        f"CREATE INDEX idx_holding_cusip ON {SCHEMA_NAME}.fund_reported_holding(issuer_cusip)",
        f"CREATE INDEX idx_holding_asset_cat ON {SCHEMA_NAME}.fund_reported_holding(asset_cat)",
        f"CREATE INDEX idx_holding_issuer ON {SCHEMA_NAME}.fund_reported_holding(issuer_name)",
        f"CREATE INDEX idx_fund_assets ON {SCHEMA_NAME}.fund_reported_info(total_assets DESC)",
        f"CREATE INDEX idx_registrant_name ON {SCHEMA_NAME}.registrant(registrant_name)",
        f"CREATE INDEX idx_identifiers_holding ON {SCHEMA_NAME}.identifiers(holding_id)",
        f"CREATE INDEX idx_debt_holding ON {SCHEMA_NAME}.debt_security(holding_id)",
    ]

    with conn.cursor() as cur:
        for idx_sql in indexes:
            try:
                cur.execute(idx_sql)
            except Exception as e:
                print(f"  Warning: {e}")
        conn.commit()

    print(f"Created {len(indexes)} indexes")

def create_views(conn):
    """Create useful views"""
    views = [
        # Fund summary view
        f"""
        CREATE OR REPLACE VIEW {SCHEMA_NAME}.fund_summary AS
        SELECT
            f.accession_number,
            f.series_name,
            r.registrant_name,
            f.total_assets,
            f.net_assets,
            COUNT(h.holding_id) as holding_count
        FROM {SCHEMA_NAME}.fund_reported_info f
        JOIN {SCHEMA_NAME}.registrant r USING (accession_number)
        LEFT JOIN {SCHEMA_NAME}.fund_reported_holding h USING (accession_number)
        GROUP BY f.accession_number, f.series_name, r.registrant_name, f.total_assets, f.net_assets
        """,

        # Top holdings view
        f"""
        CREATE OR REPLACE VIEW {SCHEMA_NAME}.top_holdings AS
        SELECT
            h.accession_number,
            f.series_name,
            h.issuer_name,
            h.issuer_cusip,
            h.percentage,
            h.currency_value,
            h.asset_cat
        FROM {SCHEMA_NAME}.fund_reported_holding h
        JOIN {SCHEMA_NAME}.fund_reported_info f USING (accession_number)
        WHERE h.percentage IS NOT NULL
        ORDER BY h.accession_number, h.percentage DESC
        """
    ]

    with conn.cursor() as cur:
        for view_sql in views:
            cur.execute(view_sql)
        conn.commit()

    print(f"Created {len(views)} views")

def main():
    print("=" * 60)
    print("LOADING DATA INTO POSTGRESQL")
    print("=" * 60)
    print(f"\nConnecting to: {DB_CONFIG['host']}")
    print(f"Database: {DB_CONFIG['database']}")
    print(f"Schema: {SCHEMA_NAME}")

    conn = get_connection()
    print("Connected successfully!")

    # Create schema and tables
    print("\nCreating schema and tables...")
    create_schema(conn)
    create_tables(conn)

    # Load data
    print("\nLoading data...")
    total_rows = 0
    for filename, table_name in FILES_TO_LOAD:
        rows = load_table(conn, filename, table_name)
        total_rows += rows
        print(f"  {table_name}: {rows:,} rows")

    # Create indexes
    print("\nCreating indexes...")
    create_indexes(conn)

    # Create views
    print("\nCreating views...")
    create_views(conn)

    # Verify
    print("\nVerifying data...")
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {SCHEMA_NAME}.fund_reported_info")
        fund_count = cur.fetchone()[0]
        cur.execute(f"SELECT COUNT(*) FROM {SCHEMA_NAME}.fund_reported_holding")
        holding_count = cur.fetchone()[0]
        cur.execute(f"SELECT SUM(total_assets) FROM {SCHEMA_NAME}.fund_reported_info")
        total_aum = cur.fetchone()[0]

    print(f"  Funds loaded: {fund_count}")
    print(f"  Holdings loaded: {holding_count:,}")
    print(f"  Total AUM: ${total_aum/1e12:.2f} Trillion")

    conn.close()

    print("\n" + "=" * 60)
    print("POSTGRESQL LOAD COMPLETE")
    print("=" * 60)
    print(f"Total rows loaded: {total_rows:,}")

if __name__ == "__main__":
    main()
