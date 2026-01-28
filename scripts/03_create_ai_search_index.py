#!/usr/bin/env python3
"""
Create Azure AI Search index for fund documents.
Sets up vector search configuration and schema.
"""

import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
)

# Load environment variables
load_dotenv("/Users/ozgurguler/Developer/Projects/af-pii-funds/.env")

# Azure AI Search configuration
SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
SEARCH_KEY = os.getenv("AZURE_SEARCH_ADMIN_KEY")
INDEX_NAME = "nport-funds-index"

def create_index():
    """Create the fund search index"""
    print("=" * 60)
    print("CREATING AZURE AI SEARCH INDEX")
    print("=" * 60)
    print(f"\nEndpoint: {SEARCH_ENDPOINT}")
    print(f"Index name: {INDEX_NAME}")

    # Create index client
    credential = AzureKeyCredential(SEARCH_KEY)
    index_client = SearchIndexClient(endpoint=SEARCH_ENDPOINT, credential=credential)

    # Define vector search configuration
    vector_search = VectorSearch(
        profiles=[
            VectorSearchProfile(
                name="fund-vector-profile",
                algorithm_configuration_name="fund-hnsw-config",
            )
        ],
        algorithms=[
            HnswAlgorithmConfiguration(
                name="fund-hnsw-config",
                parameters={
                    "m": 4,
                    "efConstruction": 400,
                    "efSearch": 500,
                    "metric": "cosine"
                }
            )
        ],
    )

    # Define index schema
    fields = [
        # Key field
        SimpleField(
            name="id",
            type=SearchFieldDataType.String,
            key=True,
            filterable=True
        ),
        # Identifiers
        SimpleField(
            name="accession_number",
            type=SearchFieldDataType.String,
            filterable=True
        ),
        SimpleField(
            name="series_id",
            type=SearchFieldDataType.String,
            filterable=True
        ),
        SimpleField(
            name="cik",
            type=SearchFieldDataType.String,
            filterable=True
        ),
        # Searchable text fields
        SearchableField(
            name="fund_name",
            type=SearchFieldDataType.String,
            searchable=True,
            filterable=True,
            sortable=True
        ),
        SearchableField(
            name="manager_name",
            type=SearchFieldDataType.String,
            searchable=True,
            filterable=True,
            facetable=True
        ),
        # Numeric fields
        SimpleField(
            name="total_assets",
            type=SearchFieldDataType.Double,
            filterable=True,
            sortable=True,
            facetable=True
        ),
        SimpleField(
            name="net_assets",
            type=SearchFieldDataType.Double,
            filterable=True,
            sortable=True
        ),
        SimpleField(
            name="holding_count",
            type=SearchFieldDataType.Int32,
            filterable=True,
            sortable=True
        ),
        # Classification fields
        SimpleField(
            name="fund_type",
            type=SearchFieldDataType.String,
            filterable=True,
            facetable=True
        ),
        SimpleField(
            name="primary_asset_class",
            type=SearchFieldDataType.String,
            filterable=True,
            facetable=True
        ),
        # Content for semantic search
        SearchableField(
            name="content",
            type=SearchFieldDataType.String,
            searchable=True
        ),
        SearchableField(
            name="top_holdings_text",
            type=SearchFieldDataType.String,
            searchable=True
        ),
        SearchableField(
            name="allocation_text",
            type=SearchFieldDataType.String,
            searchable=True
        ),
        # Vector field
        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=1536,
            vector_search_profile_name="fund-vector-profile"
        ),
    ]

    # Create the index
    index = SearchIndex(
        name=INDEX_NAME,
        fields=fields,
        vector_search=vector_search
    )

    print("\nCreating index...")
    try:
        # Delete if exists
        try:
            index_client.delete_index(INDEX_NAME)
            print(f"  Deleted existing index: {INDEX_NAME}")
        except:
            pass

        # Create new index
        result = index_client.create_index(index)
        print(f"  Created index: {result.name}")
        print(f"  Fields: {len(result.fields)}")

    except Exception as e:
        print(f"Error creating index: {e}")
        raise

    print("\n" + "=" * 60)
    print("INDEX CREATED SUCCESSFULLY")
    print("=" * 60)
    print(f"""
Index: {INDEX_NAME}
Fields:
  - id (key)
  - accession_number, series_id, cik (identifiers)
  - fund_name, manager_name (searchable text)
  - total_assets, net_assets, holding_count (numeric)
  - fund_type, primary_asset_class (filters)
  - content, top_holdings_text, allocation_text (searchable)
  - content_vector (1536-dim vector for semantic search)
""")

if __name__ == "__main__":
    create_index()
