#!/usr/bin/env python3
"""
Generate fund documents and upload to Azure AI Search.
Creates embeddings using Azure OpenAI text-embedding-3-small.
"""

import os
import sqlite3
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

# Load environment variables
load_dotenv("/Users/ozgurguler/Developer/Projects/af-pii-funds/.env")

# Paths
DB_PATH = Path("/Users/ozgurguler/Developer/Projects/af-pii-funds/fund-rag-poc/nport_funds.db")

# Azure OpenAI configuration
OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
OPENAI_KEY = os.getenv("AZURE_OPENAI_API_KEY")
EMBEDDING_DEPLOYMENT = os.getenv("AZURE_TEXT_EMBEDDING_DEPLOYMENT_NAME", "text-embedding-3-small")

# Azure AI Search configuration
SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
SEARCH_KEY = os.getenv("AZURE_SEARCH_ADMIN_KEY")
INDEX_NAME = "nport-funds-index"

# Initialize clients
openai_client = AzureOpenAI(
    azure_endpoint=OPENAI_ENDPOINT,
    api_key=OPENAI_KEY,
    api_version="2024-02-01"
)

search_client = SearchClient(
    endpoint=SEARCH_ENDPOINT,
    index_name=INDEX_NAME,
    credential=AzureKeyCredential(SEARCH_KEY)
)

def get_embedding(text: str) -> list:
    """Get embedding from Azure OpenAI"""
    # Truncate if too long (max ~8000 tokens for this model)
    if len(text) > 30000:
        text = text[:30000]

    response = openai_client.embeddings.create(
        model=EMBEDDING_DEPLOYMENT,
        input=text
    )
    return response.data[0].embedding

def classify_fund_type(holdings: list) -> str:
    """Classify fund type based on holdings"""
    if not holdings:
        return "Unknown"

    asset_cats = {}
    for h in holdings:
        cat = h['asset_cat'] or 'OTHER'
        pct = float(h['percentage'] or 0)
        asset_cats[cat] = asset_cats.get(cat, 0) + pct

    equity_pct = asset_cats.get('EC', 0) + asset_cats.get('EP', 0)
    debt_pct = asset_cats.get('DBT', 0)
    abs_pct = sum(v for k, v in asset_cats.items() if k.startswith('ABS'))

    if equity_pct > 70:
        return "Equity"
    elif debt_pct > 70:
        return "Bond"
    elif equity_pct > 30 and debt_pct > 30:
        return "Balanced"
    elif abs_pct > 30:
        return "Fixed Income (ABS)"
    elif debt_pct > 50:
        return "Fixed Income"
    else:
        return "Multi-Asset"

def get_primary_asset_class(holdings: list) -> str:
    """Get primary asset class"""
    if not holdings:
        return "Unknown"

    asset_cats = {}
    for h in holdings:
        cat = h['asset_cat'] or 'OTHER'
        pct = float(h['percentage'] or 0)
        asset_cats[cat] = asset_cats.get(cat, 0) + pct

    if asset_cats:
        return max(asset_cats, key=asset_cats.get)
    return "Unknown"

def build_content_text(fund: dict, holdings: list, notes: list) -> str:
    """Build natural language content for embedding"""
    parts = []

    # Fund identity
    parts.append(f"{fund['series_name']} is a mutual fund managed by {fund['registrant_name']}.")

    # Size
    assets_b = float(fund['total_assets'] or 0) / 1e9
    parts.append(f"Total assets: ${assets_b:.1f} billion.")

    # Asset allocation
    if holdings:
        asset_cats = {}
        for h in holdings:
            cat = h['asset_cat'] or 'OTHER'
            pct = float(h['percentage'] or 0)
            asset_cats[cat] = asset_cats.get(cat, 0) + pct

        cat_map = {
            'EC': 'common stocks',
            'EP': 'preferred stocks',
            'DBT': 'debt securities',
            'ABS-MBS': 'mortgage-backed securities',
            'ABS-CBDO': 'collateralized debt obligations',
            'ABS-O': 'other asset-backed securities',
            'STIV': 'structured products',
            'LON': 'loans',
            'RA': 'repurchase agreements',
        }

        alloc_parts = []
        for cat, pct in sorted(asset_cats.items(), key=lambda x: -x[1])[:5]:
            if pct > 1:
                cat_name = cat_map.get(cat, cat.lower())
                alloc_parts.append(f"{cat_name} ({pct:.1f}%)")

        if alloc_parts:
            parts.append(f"Asset allocation: {', '.join(alloc_parts)}.")

    return " ".join(parts)

def build_top_holdings_text(holdings: list) -> str:
    """Build text describing top holdings"""
    if not holdings:
        return ""

    # Sort by percentage and take top 15
    sorted_holdings = sorted(holdings, key=lambda x: float(x['percentage'] or 0), reverse=True)[:15]

    if not sorted_holdings:
        return ""

    parts = ["Top holdings:"]
    for h in sorted_holdings:
        name = h['issuer_name'] or 'Unknown'
        pct = float(h['percentage'] or 0) * 100  # Convert to percentage
        if pct > 0.1:
            parts.append(f"{name} ({pct:.2f}%)")

    return " ".join(parts[:16])  # Limit length

def build_allocation_text(holdings: list) -> str:
    """Build text describing allocation"""
    if not holdings:
        return ""

    # Geographic breakdown
    countries = {}
    for h in holdings:
        country = h['investment_country'] or 'Unknown'
        pct = float(h['percentage'] or 0)
        countries[country] = countries.get(country, 0) + pct

    geo_parts = []
    for country, pct in sorted(countries.items(), key=lambda x: -x[1])[:5]:
        if pct > 1:
            geo_parts.append(f"{country}: {pct:.1f}%")

    if geo_parts:
        return f"Geographic exposure: {', '.join(geo_parts)}."
    return ""

def create_fund_document(db: sqlite3.Connection, accession_number: str) -> dict:
    """Create a complete fund document"""
    db.row_factory = sqlite3.Row

    # Get fund info
    cur = db.cursor()
    cur.execute("""
        SELECT f.*, r.registrant_name, r.cik
        FROM fund_reported_info f
        JOIN registrant r USING (accession_number)
        WHERE f.accession_number = ?
    """, [accession_number])
    fund = dict(cur.fetchone())

    # Get holdings
    cur.execute("""
        SELECT issuer_name, issuer_cusip, percentage, currency_value,
               asset_cat, investment_country
        FROM fund_reported_holding
        WHERE accession_number = ?
        ORDER BY CAST(percentage AS REAL) DESC
    """, [accession_number])
    holdings = [dict(row) for row in cur.fetchall()]

    # Get notes
    cur.execute("""
        SELECT explanatory_note FROM explanatory_note
        WHERE accession_number = ?
    """, [accession_number])
    notes = [dict(row) for row in cur.fetchall()]

    # Build document
    content = build_content_text(fund, holdings, notes)
    top_holdings_text = build_top_holdings_text(holdings)
    allocation_text = build_allocation_text(holdings)

    # Combine all text for embedding
    full_text = f"{content} {top_holdings_text} {allocation_text}"

    doc = {
        "id": accession_number.replace("-", "_"),  # AI Search requires no dashes in key
        "accession_number": accession_number,
        "series_id": fund.get('series_id', ''),
        "cik": fund.get('cik', ''),
        "fund_name": fund.get('series_name', 'Unknown'),
        "manager_name": fund.get('registrant_name', 'Unknown'),
        "total_assets": float(fund.get('total_assets') or 0),
        "net_assets": float(fund.get('net_assets') or 0),
        "holding_count": len(holdings),
        "fund_type": classify_fund_type(holdings),
        "primary_asset_class": get_primary_asset_class(holdings),
        "content": content,
        "top_holdings_text": top_holdings_text,
        "allocation_text": allocation_text,
        "content_vector": None  # Will be populated below
    }

    return doc, full_text

def main():
    print("=" * 60)
    print("UPLOADING FUND DOCUMENTS TO AZURE AI SEARCH")
    print("=" * 60)
    print(f"\nDatabase: {DB_PATH}")
    print(f"Search endpoint: {SEARCH_ENDPOINT}")
    print(f"Index: {INDEX_NAME}")
    print(f"Embedding model: {EMBEDDING_DEPLOYMENT}")

    # Connect to database
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()

    # Get all fund accession numbers
    cur.execute("SELECT accession_number FROM fund_reported_info ORDER BY CAST(total_assets AS REAL) DESC")
    accession_numbers = [row[0] for row in cur.fetchall()]

    print(f"\nProcessing {len(accession_numbers)} funds...")

    # Process in batches
    batch_size = 10
    documents = []
    total_uploaded = 0

    for i, accession in enumerate(accession_numbers):
        try:
            # Create document
            doc, full_text = create_fund_document(db, accession)

            # Get embedding
            embedding = get_embedding(full_text)
            doc["content_vector"] = embedding

            documents.append(doc)

            # Progress
            if (i + 1) % 10 == 0:
                print(f"  Processed {i + 1}/{len(accession_numbers)} funds...")

            # Upload in batches
            if len(documents) >= batch_size:
                result = search_client.upload_documents(documents)
                total_uploaded += len(documents)
                documents = []
                time.sleep(0.5)  # Rate limiting

        except Exception as e:
            print(f"  Error processing {accession}: {e}")
            continue

    # Upload remaining documents
    if documents:
        result = search_client.upload_documents(documents)
        total_uploaded += len(documents)

    db.close()

    print("\n" + "=" * 60)
    print("UPLOAD COMPLETE")
    print("=" * 60)
    print(f"Total documents uploaded: {total_uploaded}")
    print(f"Index: {INDEX_NAME}")

    # Test search
    print("\nTesting search...")
    results = search_client.search(
        search_text="large cap equity index fund",
        top=3,
        select=["fund_name", "manager_name", "total_assets"]
    )

    print("Query: 'large cap equity index fund'")
    print("Results:")
    for result in results:
        assets_b = result['total_assets'] / 1e9
        print(f"  - {result['fund_name'][:50]} | ${assets_b:.1f}B")

if __name__ == "__main__":
    main()
