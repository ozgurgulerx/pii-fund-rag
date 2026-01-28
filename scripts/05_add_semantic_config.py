#!/usr/bin/env python3
"""
Add semantic configuration to the nport-funds-index.
Required for Azure AI Foundry knowledge base integration.
"""

import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
)

# Load environment variables
load_dotenv("/Users/ozgurguler/Developer/Projects/af-pii-funds/.env")

# Azure AI Search configuration
SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
SEARCH_KEY = os.getenv("AZURE_SEARCH_ADMIN_KEY")
INDEX_NAME = "nport-funds-index"

def add_semantic_config():
    print("=" * 60)
    print("ADDING SEMANTIC CONFIGURATION")
    print("=" * 60)
    print(f"\nEndpoint: {SEARCH_ENDPOINT}")
    print(f"Index: {INDEX_NAME}")

    # Create index client
    credential = AzureKeyCredential(SEARCH_KEY)
    index_client = SearchIndexClient(endpoint=SEARCH_ENDPOINT, credential=credential)

    # Get existing index
    index = index_client.get_index(INDEX_NAME)
    print(f"\nRetrieved index: {index.name}")
    print(f"Current fields: {len(index.fields)}")

    # Define semantic configuration
    semantic_config = SemanticConfiguration(
        name="fund-semantic-config",
        prioritized_fields=SemanticPrioritizedFields(
            title_field=SemanticField(field_name="fund_name"),
            content_fields=[
                SemanticField(field_name="content"),
                SemanticField(field_name="top_holdings_text"),
                SemanticField(field_name="allocation_text"),
            ],
            keywords_fields=[
                SemanticField(field_name="manager_name"),
                SemanticField(field_name="fund_type"),
                SemanticField(field_name="primary_asset_class"),
            ]
        )
    )

    # Add semantic search to index
    index.semantic_search = SemanticSearch(
        default_configuration_name="fund-semantic-config",
        configurations=[semantic_config]
    )

    # Update the index
    print("\nUpdating index with semantic configuration...")
    result = index_client.create_or_update_index(index)

    print(f"\n✅ Semantic configuration added!")
    print(f"   Configuration name: fund-semantic-config")
    print(f"   Title field: fund_name")
    print(f"   Content fields: content, top_holdings_text, allocation_text")
    print(f"   Keyword fields: manager_name, fund_type, primary_asset_class")

    print("\n" + "=" * 60)
    print("COMPLETE - Index is now compatible with AI Foundry")
    print("=" * 60)

if __name__ == "__main__":
    add_semantic_config()
