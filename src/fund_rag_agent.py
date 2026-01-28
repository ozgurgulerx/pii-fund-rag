#!/usr/bin/env python3
"""
Fund RAG Agent - Query mutual fund data using natural language.
Combines SQL queries (SQLite) with semantic search (Azure AI Search).
"""

import os
import sqlite3
import re
from pathlib import Path
from dotenv import load_dotenv
from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from pii_filter import PiiFilter

# Load environment variables
load_dotenv("/Users/ozgurguler/Developer/Projects/af-pii-funds/.env")

# Paths
DB_PATH = Path("/Users/ozgurguler/Developer/Projects/af-pii-funds/fund-rag-poc/nport_funds.db")

# Azure OpenAI configuration
OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
OPENAI_KEY = os.getenv("AZURE_OPENAI_API_KEY")
LLM_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-5-nano")
EMBEDDING_DEPLOYMENT = os.getenv("AZURE_TEXT_EMBEDDING_DEPLOYMENT_NAME", "text-embedding-3-small")

# Azure AI Search configuration
SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
SEARCH_KEY = os.getenv("AZURE_SEARCH_ADMIN_KEY")
FUND_INDEX = "nport-funds-index"
RAPTOR_INDEX = os.getenv("RAPTOR_INDEX_NAME", "imf-weo-raptor-index")  # Your RAPTOR index


class FundRAGAgent:
    def __init__(self):
        # Initialize OpenAI client
        self.llm = AzureOpenAI(
            azure_endpoint=OPENAI_ENDPOINT,
            api_key=OPENAI_KEY,
            api_version="2024-06-01"
        )

        # Initialize Search clients
        credential = AzureKeyCredential(SEARCH_KEY)
        self.fund_search = SearchClient(
            endpoint=SEARCH_ENDPOINT,
            index_name=FUND_INDEX,
            credential=credential
        )

        # Try to connect to RAPTOR index if it exists
        try:
            self.raptor_search = SearchClient(
                endpoint=SEARCH_ENDPOINT,
                index_name=RAPTOR_INDEX,
                credential=credential
            )
            self.has_raptor = True
        except:
            self.raptor_search = None
            self.has_raptor = False

        # SQLite connection - check_same_thread=False allows use across Flask threads
        self.db = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.db.row_factory = sqlite3.Row

        # PII filter
        self.pii_filter = PiiFilter()
        if self.pii_filter.is_available():
            print("PII filter enabled")
        else:
            print("Warning: PII filter unavailable")

    def get_embedding(self, text: str) -> list:
        """Get embedding from Azure OpenAI"""
        response = self.llm.embeddings.create(
            model=EMBEDDING_DEPLOYMENT,
            input=text[:8000]  # Truncate if too long
        )
        return response.data[0].embedding

    def route_query(self, query: str) -> dict:
        """Classify query type using LLM"""
        system_prompt = """You are a query router for a mutual fund Q&A system.
Classify the user's query into one of these categories:

1. SQL - Questions requiring precise data: rankings, specific fund lookups, holdings by CUSIP,
   comparisons, aggregations, "top N", "largest", "which funds hold X"
   Examples: "Top 10 bond funds", "What does PIMCO Income hold?", "Funds holding Apple stock"

2. SEMANTIC - Questions requiring understanding/similarity: fund descriptions, investment styles,
   "funds like X", general characteristics
   Examples: "Conservative income funds", "Funds similar to Vanguard 500", "Growth-oriented ETFs"

3. HYBRID - Questions needing both precise data AND semantic understanding
   Examples: "Top growth funds with tech exposure", "Largest bond funds focused on MBS"

Return JSON only: {"route": "SQL|SEMANTIC|HYBRID", "reasoning": "brief explanation"}"""

        response = self.llm.chat.completions.create(
            model=LLM_DEPLOYMENT,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            response_format={"type": "json_object"}
        )

        import json
        return json.loads(response.choices[0].message.content)

    def generate_sql(self, query: str) -> str:
        """Generate SQL from natural language"""
        schema_info = """
Available tables:
- fund_reported_info: accession_number, series_name, total_assets, net_assets
- registrant: accession_number, registrant_name, cik
- fund_reported_holding: accession_number, holding_id, issuer_name, issuer_cusip,
  percentage (decimal 0-1), currency_value, asset_cat (EC=equity, DBT=debt, ABS-MBS=mortgage-backed)
- debt_security: holding_id, maturity_date, coupon_type, annualized_rate
- monthly_total_return: accession_number, monthly_total_return1/2/3

Common joins:
- fund_reported_info JOIN registrant USING (accession_number)
- fund_reported_holding JOIN fund_reported_info USING (accession_number)

Notes:
- total_assets and percentage are stored as TEXT, use CAST(x AS REAL) for numeric operations
- percentage is decimal (0.05 = 5%), multiply by 100 for display
"""

        system_prompt = f"""You are a SQL expert. Generate SQLite-compatible SQL for the user's question.
{schema_info}

Rules:
- Return ONLY the SQL query, no explanation
- Always include fund name (series_name) and manager (registrant_name) in results
- Use CAST(total_assets AS REAL) for numeric comparisons
- Limit results to 20 unless user specifies otherwise
- For holdings, multiply percentage by 100 for display"""

        response = self.llm.chat.completions.create(
            model=LLM_DEPLOYMENT,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]
        )

        sql = response.choices[0].message.content.strip()
        # Clean up SQL (remove markdown code blocks if present)
        sql = re.sub(r'```sql\n?', '', sql)
        sql = re.sub(r'```\n?', '', sql)
        return sql.strip()

    def execute_sql(self, sql: str) -> list:
        """Execute SQL and return results"""
        try:
            cur = self.db.cursor()
            cur.execute(sql)
            rows = cur.fetchall()
            # Convert to list of dicts
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            return [{"error": str(e), "sql": sql}]

    def search_funds_semantic(self, query: str, top: int = 5, filters: str = None) -> list:
        """Search funds using semantic similarity"""
        embedding = self.get_embedding(query)

        vector_query = VectorizedQuery(
            vector=embedding,
            k_nearest_neighbors=top,
            fields="content_vector"
        )

        results = self.fund_search.search(
            search_text=query,
            vector_queries=[vector_query],
            filter=filters,
            top=top,
            select=["fund_name", "manager_name", "total_assets", "fund_type", "content", "top_holdings_text"]
        )

        return list(results)

    def search_raptor(self, query: str, top: int = 3) -> list:
        """Search RAPTOR index for macro context"""
        if not self.has_raptor:
            return []

        try:
            embedding = self.get_embedding(query)
            vector_query = VectorizedQuery(
                vector=embedding,
                k_nearest_neighbors=top,
                fields="content_vector"
            )

            results = self.raptor_search.search(
                search_text=query,
                vector_queries=[vector_query],
                top=top
            )
            return list(results)
        except:
            return []

    def synthesize_answer(self, query: str, context: dict) -> str:
        """Generate natural language answer from context"""
        system_prompt = """You are a helpful mutual fund analyst assistant.
Answer the user's question based on the provided context.
Be concise but informative. Format numbers nicely (e.g., $2.5B instead of 2500000000).
If showing fund data, format it as a clear list or table."""

        context_str = f"""
Query: {query}

Data retrieved:
{context}
"""

        response = self.llm.chat.completions.create(
            model=LLM_DEPLOYMENT,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context_str}
            ]
        )

        return response.choices[0].message.content

    def answer(self, query: str) -> str:
        """Main entry point - answer a user query"""
        print(f"\n🔍 Query: {query}")

        # Step 0: Check for PII before processing
        pii_result = self.pii_filter.check(query)
        if pii_result.has_pii:
            warning = self.pii_filter.format_warning(pii_result.entities)
            print(f"🚫 PII DETECTED - Query blocked")
            print(f"   Categories: {[e.category for e in pii_result.entities]}")
            return warning

        # Step 1: Route the query
        route_result = self.route_query(query)
        route = route_result.get("route", "HYBRID")
        print(f"📍 Route: {route} - {route_result.get('reasoning', '')}")

        context = {}

        # Step 2: Execute based on route
        if route == "SQL":
            sql = self.generate_sql(query)
            print(f"📊 SQL: {sql[:100]}...")
            results = self.execute_sql(sql)
            context["sql_results"] = results

        elif route == "SEMANTIC":
            results = self.search_funds_semantic(query)
            context["semantic_results"] = [
                {
                    "fund_name": r["fund_name"],
                    "manager": r["manager_name"],
                    "assets": f"${r['total_assets']/1e9:.1f}B",
                    "type": r["fund_type"],
                    "description": r["content"][:200]
                }
                for r in results
            ]

        else:  # HYBRID
            # Get both SQL and semantic results
            sql = self.generate_sql(query)
            print(f"📊 SQL: {sql[:100]}...")
            sql_results = self.execute_sql(sql)
            context["sql_results"] = sql_results

            semantic_results = self.search_funds_semantic(query, top=3)
            context["semantic_context"] = [r["content"] for r in semantic_results]

        # Step 3: Synthesize answer
        answer = self.synthesize_answer(query, context)

        return answer


def main():
    """Interactive demo"""
    print("=" * 60)
    print("FUND RAG AGENT - Interactive Demo")
    print("=" * 60)
    print("\nType your questions about mutual funds. Type 'quit' to exit.\n")

    agent = FundRAGAgent()

    # Sample queries to try
    sample_queries = [
        "What are the top 5 largest funds?",
        "Tell me about PIMCO Income Fund",
        "Which funds hold NVIDIA stock?",
        "Show me conservative bond funds",
        "Compare Vanguard 500 vs Fidelity 500 Index",
    ]

    print("Sample queries you can try:")
    for i, q in enumerate(sample_queries, 1):
        print(f"  {i}. {q}")
    print()

    while True:
        try:
            query = input("\n💬 You: ").strip()
            if not query:
                continue
            if query.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break

            answer = agent.answer(query)
            print(f"\n🤖 Assistant:\n{answer}")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
