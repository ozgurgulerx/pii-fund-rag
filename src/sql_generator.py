#!/usr/bin/env python3
"""
Enhanced SQL Generator with full 15-table schema support.
Generates SQLite-compatible SQL from natural language queries.
"""

import os
import re
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv("/Users/ozgurguler/Developer/Projects/af-pii-funds/.env")

# Full schema documentation for LLM
FULL_SCHEMA = """
## SQLite Database Schema - nport_funds.db

### Core Fund Tables

**fund_reported_info** (250 funds)
Primary fund data with financials and risk metrics.
Columns: accession_number (PK), series_name, series_id, series_lei, total_assets,
total_liabilities, net_assets, assets_invested, borrowing_pay_within_1yr,
credit_spread_3mon_invest, credit_spread_1yr_invest, credit_spread_5yr_invest,
credit_spread_10yr_invest, credit_spread_30yr_invest, credit_spread_3mon_noninvest,
credit_spread_1yr_noninvest, credit_spread_5yr_noninvest, credit_spread_10yr_noninvest,
credit_spread_30yr_noninvest, net_realize_gain_nonderiv_mon1, net_unrealize_ap_nonderiv_mon1,
sales_flow_mon1, reinvestment_flow_mon1, redemption_flow_mon1 (and mon2, mon3)

**registrant** (250 records)
Fund manager/company information.
Columns: accession_number (PK, FK), cik, registrant_name, file_num, lei,
address1, address2, city, state, country, zip, phone

**submission** (250 records)
Filing metadata.
Columns: accession_number (PK), filing_date, file_num, sub_type,
report_ending_period, report_date, is_last_filing

### Holdings Tables

**fund_reported_holding** (490,447 holdings)
Individual security positions held by each fund.
Columns: accession_number (FK), holding_id, issuer_name, issuer_lei, issuer_title,
issuer_cusip, balance, unit, currency_code, currency_value, exchange_rate,
percentage (decimal 0-1, multiply by 100 for %), payoff_profile,
asset_cat (EC=equity, DBT=debt, ABS-MBS=mortgage-backed, etc.),
issuer_type, investment_country, is_restricted_security, fair_value_level, derivative_cat
Primary Key: (accession_number, holding_id)

**identifiers** (572,768 records)
Security identifiers (ISIN, ticker, CUSIP).
Columns: holding_id (FK), identifiers_id, identifier_isin, identifier_ticker,
other_identifier, other_identifier_desc
Primary Key: (holding_id, identifiers_id)

### Fixed Income Tables

**debt_security** (305,413 bonds)
Bond and debt instrument details.
Columns: holding_id (PK, FK), maturity_date, coupon_type (Fixed, Floating, etc.),
annualized_rate, is_default, are_any_interest_payment,
is_any_portion_interest_paid, is_convtible_mandatory, is_convtible_contingent

**interest_rate_risk** (303 records)
Interest rate sensitivity metrics (DV01/DV100) by currency.
Columns: accession_number (FK), interest_rate_risk_id, currency_code,
intrst_rate_change_3mon_dv01, intrst_rate_change_1yr_dv01, intrst_rate_change_5yr_dv01,
intrst_rate_change_10yr_dv01, intrst_rate_change_30yr_dv01,
intrst_rate_change_3mon_dv100, intrst_rate_change_1yr_dv100, intrst_rate_change_5yr_dv100,
intrst_rate_change_10yr_dv100, intrst_rate_change_30yr_dv100
Primary Key: (accession_number, interest_rate_risk_id)

### Performance Tables

**monthly_total_return** (1,153 records)
3-month rolling returns by share class.
Columns: accession_number (FK), monthly_total_return_id, class_id,
monthly_total_return1, monthly_total_return2, monthly_total_return3
Primary Key: (accession_number, monthly_total_return_id)

**monthly_return_cat_instrument** (7,068 records)
Returns by asset category and instrument type.
Columns: accession_number, asset_cat, instrument_kind, net_realized_gain_mon1,
net_unrealized_ap_mon1, net_realized_gain_mon2, net_unrealized_ap_mon2,
net_realized_gain_mon3, net_unrealized_ap_mon3

### Derivatives Tables

**derivative_counterparty** (23,219 records)
Counterparty information for derivative positions.
Columns: holding_id (FK), derivative_counterparty_id, derivative_counterparty_name,
derivative_counterparty_lei
Primary Key: (holding_id, derivative_counterparty_id)

**fwd_foreigncur_contract_swap** (8,891 records)
Forward currency contracts and swaps.
Columns: holding_id, currency_sold_amount, desc_currency_sold,
currency_purchased_amount, desc_currency_purchased, settlement_date, unrealized_appreciation

**nonforeign_exchange_swap** (12,114 records)
Non-FX swap contracts (interest rate swaps, etc.).
Columns: holding_id, swap_flag, termination_date, upfront_payment, pmnt_currency_code,
upfront_receipt, rcpt_currency_code, notional_amount, currency_code, unrealized_appreciation

### Lending & Borrowing Tables

**securities_lending** (489,885 records)
Securities lending activity per holding.
Columns: holding_id (PK, FK), is_cash_collateral, cash_collateral_amount,
is_non_cash_collateral, non_cash_collateral_value, is_loan_by_fund, loan_value

**borrower** (2,116 records)
Fund borrowing/leverage information.
Columns: accession_number (FK), borrower_id, name, lei, aggregate_value
Primary Key: (accession_number, borrower_id)

### Other Tables

**explanatory_note** (201 notes)
Fund-specific explanatory text notes.
Columns: accession_number (FK), explanatory_note_id, item_no, explanatory_note

### Views

**fund_summary**
Pre-joined view: fund_reported_info + registrant + holdings count.
Columns: accession_number, series_name, registrant_name, total_assets, net_assets, holding_count

### Asset Category Codes (asset_cat)
- EC = Equity Common
- EP = Equity Preferred
- DBT = Debt Securities
- ABS-MBS = Mortgage-Backed Securities
- ABS-CBDO = Collateralized Debt Obligations
- ABS-O = Other Asset-Backed
- STIV = Structured Products
- LON = Loans
- RA = Repurchase Agreements
- RE = Real Estate
- COMM = Commodities

### Key Relationships
- fund_reported_info.accession_number = registrant.accession_number
- fund_reported_holding.accession_number = fund_reported_info.accession_number
- fund_reported_holding.holding_id = debt_security.holding_id
- fund_reported_holding.holding_id = identifiers.holding_id
- fund_reported_holding.holding_id = securities_lending.holding_id
- fund_reported_holding.holding_id = derivative_counterparty.holding_id
- fund_reported_info.accession_number = interest_rate_risk.accession_number
- fund_reported_info.accession_number = monthly_total_return.accession_number
"""

SYSTEM_PROMPT = f"""You are an expert SQL generator for a mutual fund database.
Generate SQLite-compatible SQL queries based on natural language questions.

{FULL_SCHEMA}

## Rules:
1. Return ONLY the SQL query, no explanations
2. Always include fund name (series_name) and manager (registrant_name) when relevant
3. Use CAST(column AS REAL) for numeric comparisons on TEXT columns
4. Percentage column is decimal (0.05 = 5%), multiply by 100 for display
5. Use proper JOINs based on the key relationships
6. Limit results to 20 unless user specifies otherwise
7. For "top N" queries, use ORDER BY and LIMIT
8. Handle NULL values appropriately with COALESCE or IS NOT NULL
9. Use table aliases for readability (f for fund_reported_info, r for registrant, h for holdings)

## Example Queries:

Q: "Top 5 largest funds"
SELECT f.series_name, r.registrant_name, CAST(f.total_assets AS REAL) as total_assets
FROM fund_reported_info f
JOIN registrant r USING (accession_number)
ORDER BY CAST(f.total_assets AS REAL) DESC
LIMIT 5

Q: "Funds holding Apple stock"
SELECT f.series_name, r.registrant_name, h.issuer_name, CAST(h.percentage AS REAL)*100 as pct
FROM fund_reported_holding h
JOIN fund_reported_info f USING (accession_number)
JOIN registrant r USING (accession_number)
WHERE h.issuer_name LIKE '%Apple%' OR h.issuer_cusip = '037833100'
ORDER BY CAST(h.percentage AS REAL) DESC
LIMIT 20

Q: "Bond funds with highest interest rate risk"
SELECT f.series_name, r.registrant_name,
       CAST(ir.intrst_rate_change_1yr_dv01 AS REAL) as dv01_1yr,
       CAST(ir.intrst_rate_change_5yr_dv01 AS REAL) as dv01_5yr
FROM fund_reported_info f
JOIN registrant r USING (accession_number)
JOIN interest_rate_risk ir USING (accession_number)
WHERE ir.currency_code = 'USD'
ORDER BY CAST(ir.intrst_rate_change_5yr_dv01 AS REAL) DESC
LIMIT 10

Q: "Maturity profile of bonds in PIMCO Income Fund"
SELECT d.maturity_date, d.coupon_type, CAST(d.annualized_rate AS REAL) as rate,
       h.issuer_name, CAST(h.currency_value AS REAL) as value
FROM fund_reported_holding h
JOIN fund_reported_info f USING (accession_number)
JOIN debt_security d ON h.holding_id = d.holding_id
WHERE f.series_name LIKE '%PIMCO Income%'
ORDER BY d.maturity_date
LIMIT 20

Q: "Funds with securities lending activity"
SELECT f.series_name, r.registrant_name,
       SUM(CAST(sl.loan_value AS REAL)) as total_loan_value,
       COUNT(*) as positions_on_loan
FROM fund_reported_holding h
JOIN fund_reported_info f USING (accession_number)
JOIN registrant r USING (accession_number)
JOIN securities_lending sl ON h.holding_id = sl.holding_id
WHERE sl.is_loan_by_fund = 'Y' OR CAST(sl.loan_value AS REAL) > 0
GROUP BY f.accession_number
ORDER BY total_loan_value DESC
LIMIT 10
"""


class SQLGenerator:
    """Generate SQL queries from natural language using LLM."""

    def __init__(self):
        self.client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2024-06-01"
        )
        self.model = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-5-nano")

    def generate(self, query: str) -> str:
        """
        Generate SQL from natural language query.

        Args:
            query: Natural language question about funds

        Returns:
            SQLite-compatible SQL query string
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": query}
            ]
        )

        sql = response.choices[0].message.content.strip()

        # Clean up SQL (remove markdown code blocks if present)
        sql = re.sub(r'```sql\n?', '', sql)
        sql = re.sub(r'```\n?', '', sql)
        sql = sql.strip()

        return sql

    def generate_with_context(self, query: str, context: str = None) -> str:
        """
        Generate SQL with additional context (e.g., from RAPTOR).

        Args:
            query: Natural language question
            context: Additional context like macro outlook

        Returns:
            SQL query string
        """
        if context:
            enhanced_query = f"{query}\n\nAdditional context: {context}"
        else:
            enhanced_query = query

        return self.generate(enhanced_query)


# Convenience function
def generate_sql(query: str) -> str:
    """Generate SQL from natural language query."""
    generator = SQLGenerator()
    return generator.generate(query)


if __name__ == "__main__":
    # Test the generator
    generator = SQLGenerator()

    test_queries = [
        "Top 5 largest bond funds",
        "Which funds hold NVIDIA stock?",
        "Funds with highest interest rate risk (DV01)",
        "Show me the maturity profile of bonds in Vanguard Total Bond Fund",
        "Funds with the most securities lending activity",
        "Compare total assets of Vanguard 500 vs Fidelity 500",
    ]

    print("=" * 70)
    print("SQL GENERATOR TEST")
    print("=" * 70)

    for query in test_queries:
        print(f"\n📝 Query: {query}")
        print("-" * 50)
        sql = generator.generate(query)
        print(f"📊 SQL:\n{sql}")
        print()
