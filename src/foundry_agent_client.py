#!/usr/bin/env python3
"""
Client to call Azure AI Foundry IQ Agent in workflows.
Use this to integrate funds-foundry-IQ-agent into your applications.
"""

import os
import requests
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential, AzureCliCredential

load_dotenv("/Users/ozgurguler/Developer/Projects/af-pii-funds/.env")


class FoundryAgentClient:
    """Client for Azure AI Foundry IQ Agent"""

    def __init__(self, agent_name: str = "funds-foundry-IQ-agent"):
        self.agent_name = agent_name
        self.project_name = "ozgurguler-7212"
        self.subscription_id = "a20bc194-9787-44ee-9c7f-7c3130e651b6"
        self.resource_group = "rg-openai"

        # Get credential
        self.credential = AzureCliCredential()

        # AI Foundry endpoint
        self.endpoint = "https://eastus2.api.azureml.ms"

    def get_token(self) -> str:
        """Get Azure AD token"""
        token = self.credential.get_token("https://management.azure.com/.default")
        return token.token

    def chat(self, message: str, conversation_history: list = None) -> dict:
        """
        Send a message to the Foundry IQ agent.

        Args:
            message: User's question
            conversation_history: Optional list of previous messages

        Returns:
            dict with 'answer' and 'citations'
        """
        # For now, this uses the direct index approach since Foundry Agents API is in preview
        # Once GA, replace with actual Foundry Agent API call

        from fund_rag_agent import FundRAGAgent
        agent = FundRAGAgent()

        answer = agent.answer(message)

        return {
            "answer": answer,
            "agent": self.agent_name,
            "source": "funds-kb02"
        }


class FoundryAgentWorkflow:
    """
    Workflow integration for Foundry IQ Agent.
    Use this class to integrate the agent into larger workflows.
    """

    def __init__(self):
        self.client = FoundryAgentClient()
        self.conversation_history = []

    def ask(self, question: str) -> str:
        """Simple Q&A - returns just the answer"""
        result = self.client.chat(question, self.conversation_history)

        # Add to history
        self.conversation_history.append({"role": "user", "content": question})
        self.conversation_history.append({"role": "assistant", "content": result["answer"]})

        return result["answer"]

    def ask_with_context(self, question: str, context: dict = None) -> dict:
        """
        Q&A with additional context.

        Args:
            question: User's question
            context: Additional context like user preferences, constraints

        Returns:
            Full response with answer, citations, metadata
        """
        # Enhance question with context
        if context:
            enhanced_question = f"{question}\n\nContext: {context}"
        else:
            enhanced_question = question

        result = self.client.chat(enhanced_question)
        result["question"] = question
        result["context"] = context

        return result

    def batch_questions(self, questions: list) -> list:
        """Process multiple questions"""
        results = []
        for q in questions:
            results.append({
                "question": q,
                "answer": self.ask(q)
            })
        return results

    def reset_conversation(self):
        """Clear conversation history"""
        self.conversation_history = []


# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("FOUNDRY IQ AGENT WORKFLOW TEST")
    print("=" * 60)

    workflow = FoundryAgentWorkflow()

    # Single question
    print("\n📝 Question 1: What are the top bond funds?")
    answer = workflow.ask("What are the top bond funds?")
    print(f"\n🤖 Answer:\n{answer}")

    # Follow-up (uses conversation history)
    print("\n" + "-" * 60)
    print("\n📝 Question 2: How might interest rates affect them?")
    answer = workflow.ask("How might interest rates affect them?")
    print(f"\n🤖 Answer:\n{answer}")

    # With context
    print("\n" + "-" * 60)
    print("\n📝 Question 3: With context (risk-averse investor)")
    result = workflow.ask_with_context(
        "What funds should I consider?",
        context={"risk_tolerance": "low", "investment_horizon": "5 years"}
    )
    print(f"\n🤖 Answer:\n{result['answer']}")

    print("\n" + "=" * 60)
    print("✅ Workflow test complete")
    print("=" * 60)
