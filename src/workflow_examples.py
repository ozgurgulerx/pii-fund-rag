#!/usr/bin/env python3
"""
Example workflows using the Foundry IQ Agent.
Shows different integration patterns for your applications.
"""

import sys
sys.path.insert(0, '/Users/ozgurguler/Developer/Projects/af-pii-funds/fund-rag-poc/src')

from fund_rag_agent import FundRAGAgent


# =============================================================================
# WORKFLOW 1: Simple Function Call
# =============================================================================

def get_fund_recommendation(query: str) -> str:
    """
    Simple function to get fund recommendations.
    Use this in any Python workflow.
    """
    agent = FundRAGAgent()
    return agent.answer(query)


# =============================================================================
# WORKFLOW 2: API Endpoint (Flask/FastAPI)
# =============================================================================

def create_api_endpoint():
    """
    Example FastAPI endpoint for the agent.

    Usage:
        POST /api/ask
        Body: {"question": "What are the best bond funds?"}
    """
    from fastapi import FastAPI
    from pydantic import BaseModel

    app = FastAPI(title="Fund RAG API")
    agent = FundRAGAgent()

    class Question(BaseModel):
        question: str

    class Answer(BaseModel):
        answer: str
        source: str = "funds-kb02"

    @app.post("/api/ask", response_model=Answer)
    def ask_agent(q: Question):
        answer = agent.answer(q.question)
        return Answer(answer=answer)

    return app


# =============================================================================
# WORKFLOW 3: Batch Processing
# =============================================================================

def batch_analyze_funds(questions: list) -> list:
    """
    Process multiple questions in batch.
    Useful for report generation.
    """
    agent = FundRAGAgent()
    results = []

    for q in questions:
        print(f"Processing: {q[:50]}...")
        answer = agent.answer(q)
        results.append({
            "question": q,
            "answer": answer
        })

    return results


# =============================================================================
# WORKFLOW 4: Multi-step Analysis
# =============================================================================

def comprehensive_fund_analysis(fund_name: str) -> dict:
    """
    Multi-step analysis of a specific fund.
    Returns comprehensive report.
    """
    agent = FundRAGAgent()

    analysis = {
        "fund_name": fund_name,
        "overview": None,
        "holdings": None,
        "risk_analysis": None,
        "macro_context": None
    }

    # Step 1: Overview
    analysis["overview"] = agent.answer(f"Tell me about {fund_name}")

    # Step 2: Holdings
    analysis["holdings"] = agent.answer(f"What are the top holdings of {fund_name}?")

    # Step 3: Risk
    analysis["risk_analysis"] = agent.answer(
        f"What are the risks of investing in {fund_name} given current market conditions?"
    )

    # Step 4: Macro context
    analysis["macro_context"] = agent.answer(
        f"How might the IMF economic outlook affect {fund_name}?"
    )

    return analysis


# =============================================================================
# WORKFLOW 5: Conditional Logic
# =============================================================================

def smart_fund_selector(
    risk_tolerance: str,  # "low", "medium", "high"
    investment_goal: str,  # "income", "growth", "balanced"
    time_horizon: str      # "short", "medium", "long"
) -> str:
    """
    Smart fund selection based on investor profile.
    """
    agent = FundRAGAgent()

    # Build query based on profile
    profile_query = f"""
    I'm looking for fund recommendations for an investor with:
    - Risk tolerance: {risk_tolerance}
    - Investment goal: {investment_goal}
    - Time horizon: {time_horizon}

    What funds would you recommend and why?
    """

    return agent.answer(profile_query)


# =============================================================================
# WORKFLOW 6: Report Generator
# =============================================================================

def generate_market_report() -> str:
    """
    Generate a comprehensive market report combining fund data and IMF outlook.
    """
    agent = FundRAGAgent()

    sections = []

    # Market overview
    sections.append("# Market Overview")
    sections.append(agent.answer("What is the current IMF economic outlook?"))

    # Top funds
    sections.append("\n# Top Funds by Category")
    sections.append("\n## Equity Funds")
    sections.append(agent.answer("What are the largest equity index funds?"))
    sections.append("\n## Bond Funds")
    sections.append(agent.answer("What are the largest bond funds?"))

    # Recommendations
    sections.append("\n# Strategic Recommendations")
    sections.append(agent.answer(
        "Given current economic conditions, how should investors position their portfolios?"
    ))

    return "\n\n".join(sections)


# =============================================================================
# MAIN - Demo the workflows
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("WORKFLOW EXAMPLES")
    print("=" * 70)

    # Demo: Simple function call
    print("\n📌 WORKFLOW 1: Simple Function Call")
    print("-" * 50)
    result = get_fund_recommendation("Top 3 bond funds?")
    print(result[:500] + "...")

    # Demo: Smart selector
    print("\n\n📌 WORKFLOW 5: Smart Fund Selector")
    print("-" * 50)
    result = smart_fund_selector(
        risk_tolerance="low",
        investment_goal="income",
        time_horizon="medium"
    )
    print(result[:500] + "...")

    print("\n" + "=" * 70)
    print("✅ See workflow_examples.py for more patterns")
    print("=" * 70)
