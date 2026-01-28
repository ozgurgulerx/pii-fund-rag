#!/usr/bin/env python3
"""
Query Router - Classifies queries into retrieval paths.
Routes: SQL, SEMANTIC, RAPTOR, HYBRID, CHAIN
"""

import os
import json
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv("/Users/ozgurguler/Developer/Projects/af-pii-funds/.env")

ROUTING_PROMPT = """You are a query router for a mutual fund Q&A system with multiple data sources.

## Available Data Sources

1. **SQL Database** (SQLite)
   - 15 tables with structured fund data
   - 250 funds, 490K holdings
   - Precise data: assets, holdings, CUSIP, percentages, risk metrics
   - Best for: rankings, comparisons, specific lookups, aggregations

2. **Semantic Index** (nport-funds-index)
   - 250 fund documents with embeddings
   - Natural language fund descriptions
   - Best for: similarity search, style matching, descriptive queries

3. **RAPTOR Index** (imf_raptor)
   - IMF World Economic Outlook documents
   - Hierarchical summaries (chunks → summaries)
   - Best for: macro context, inflation, rates, economic outlook

## Route Definitions

**SQL** - Use when query needs precise, structured data:
- "Top N", "largest", "smallest", "compare"
- "Which funds hold [security]", "CUSIP lookup"
- "Funds with [metric] > X", filters, aggregations
- Specific fund details, holdings breakdown
- Interest rate risk, DV01, performance metrics

**SEMANTIC** - Use when query needs understanding/similarity:
- "Similar to", "like", "funds that resemble"
- Investment style: "conservative", "growth-oriented", "income-focused"
- Descriptive: "tell me about", general characteristics
- No specific numbers needed

**RAPTOR** - Use when query is about macro/economic context:
- "IMF", "World Economic Outlook"
- "Inflation outlook", "interest rate forecast"
- "Economic conditions", "growth forecast"
- Regional outlooks: "emerging markets", "US economy"

**HYBRID** - Use when query needs BOTH fund data AND macro context:
- "Best funds given current rate environment"
- "Bond funds and interest rate risk outlook"
- "How might [economic event] affect [fund type]"
- Combines SQL/Semantic with RAPTOR in parallel

**CHAIN** - Use when macro context should DRIVE fund selection:
- "Best funds IF inflation rises"
- "Position portfolio for IMF outlook"
- "Where to invest given [economic scenario]"
- First gets RAPTOR context, then derives fund criteria, then queries funds

## Output Format

Return JSON only:
{
    "route": "SQL|SEMANTIC|RAPTOR|HYBRID|CHAIN",
    "reasoning": "Brief explanation of why this route",
    "sql_hint": "Optional hint for SQL generation if route is SQL/HYBRID/CHAIN",
    "raptor_topics": ["inflation", "rates"] // Optional topics for RAPTOR search
}
"""


class QueryRouter:
    """Routes queries to appropriate retrieval paths."""

    def __init__(self):
        self.client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2024-06-01"
        )
        self.model = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-5-nano")

    def route(self, query: str) -> dict:
        """
        Classify a query into a retrieval route.

        Args:
            query: User's natural language question

        Returns:
            dict with route, reasoning, and optional hints
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": ROUTING_PROMPT},
                {"role": "user", "content": query}
            ],
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)

        # Ensure required fields
        if "route" not in result:
            result["route"] = "HYBRID"  # Default to hybrid if unclear
        if "reasoning" not in result:
            result["reasoning"] = "Default routing"

        return result

    def quick_route(self, query: str) -> str:
        """
        Quick route classification using keyword heuristics.
        Faster but less accurate than LLM routing.

        Args:
            query: User's question

        Returns:
            Route string: SQL, SEMANTIC, RAPTOR, HYBRID, or CHAIN
        """
        query_lower = query.lower()

        # RAPTOR indicators (macro/economic)
        raptor_keywords = [
            "imf", "inflation", "economic outlook", "interest rate forecast",
            "gdp", "growth forecast", "monetary policy", "fed", "central bank",
            "recession", "emerging market outlook", "world economic"
        ]
        if any(kw in query_lower for kw in raptor_keywords):
            # Check if also asking about funds
            fund_keywords = ["fund", "invest", "portfolio", "position", "best", "recommend"]
            if any(kw in query_lower for kw in fund_keywords):
                if any(cond in query_lower for cond in ["if", "given", "based on", "considering"]):
                    return "CHAIN"
                return "HYBRID"
            return "RAPTOR"

        # SQL indicators (precise data)
        sql_keywords = [
            "top", "largest", "smallest", "compare", "list", "show me",
            "which funds hold", "cusip", "isin", "ticker",
            "how many", "total", "sum", "average", "count",
            "greater than", "less than", "between",
            "dv01", "interest rate risk", "maturity", "holdings of"
        ]
        if any(kw in query_lower for kw in sql_keywords):
            return "SQL"

        # SEMANTIC indicators (similarity/style)
        semantic_keywords = [
            "similar to", "like", "resemble", "style",
            "conservative", "aggressive", "growth-oriented", "income-focused",
            "tell me about", "describe", "what kind of"
        ]
        if any(kw in query_lower for kw in semantic_keywords):
            return "SEMANTIC"

        # Default to SQL for most fund queries
        if any(kw in query_lower for kw in ["fund", "etf", "bond", "equity", "stock"]):
            return "SQL"

        # Default to HYBRID if unclear
        return "HYBRID"


# Convenience function
def route_query(query: str, use_llm: bool = True) -> dict:
    """
    Route a query to the appropriate retrieval path.

    Args:
        query: User's question
        use_llm: Whether to use LLM (True) or heuristics (False)

    Returns:
        Routing result dict
    """
    router = QueryRouter()
    if use_llm:
        return router.route(query)
    else:
        return {"route": router.quick_route(query), "reasoning": "Heuristic routing"}


if __name__ == "__main__":
    # Test the router
    router = QueryRouter()

    test_queries = [
        ("Top 5 largest bond funds", "SQL"),
        ("Funds similar to Vanguard 500", "SEMANTIC"),
        ("What is IMF's inflation outlook?", "RAPTOR"),
        ("Best bond funds given current rate environment", "HYBRID"),
        ("How should I position my portfolio for IMF's growth forecast?", "CHAIN"),
        ("Which funds hold Apple stock?", "SQL"),
        ("Conservative income-focused funds", "SEMANTIC"),
        ("Compare Vanguard Total Bond vs PIMCO Income", "SQL"),
    ]

    print("=" * 70)
    print("QUERY ROUTER TEST")
    print("=" * 70)

    for query, expected in test_queries:
        print(f"\n📝 Query: {query}")
        print(f"   Expected: {expected}")

        # Test heuristic routing
        quick = router.quick_route(query)
        print(f"   Heuristic: {quick} {'✓' if quick == expected else '✗'}")

        # Test LLM routing
        result = router.route(query)
        print(f"   LLM Route: {result['route']} {'✓' if result['route'] == expected else '✗'}")
        print(f"   Reasoning: {result['reasoning']}")
