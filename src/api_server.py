#!/usr/bin/env python3
"""
Flask API Server for Fund RAG Backend.
Provides HTTP endpoints for the Next.js frontend.
"""

import sys
sys.path.insert(0, '/Users/ozgurguler/Developer/Projects/af-pii-funds/fund-rag-poc/src')

import json
import threading
import queue
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from unified_retriever import UnifiedRetriever
from foundry_agent_client import FoundryAgentClient
from query_router import QueryRouter

app = Flask(__name__)
CORS(app)  # Enable CORS for Next.js frontend

# Initialize retrievers once
print("Initializing Fund RAG retriever...")
retriever = UnifiedRetriever()
print("Retriever ready!")

print("Initializing Foundry IQ client...")
foundry_client = FoundryAgentClient()
print("Foundry IQ client ready!")

# Router for quick route detection
router = QueryRouter()


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "service": "fund-rag-api"})


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Main chat endpoint for fund queries.

    Request body:
        {
            "message": "What are the top 5 bond funds?",
            "retrieval_mode": "code-rag" | "foundry-iq"
        }

    Response:
        {
            "answer": "...",
            "route": "SQL|SEMANTIC|RAPTOR|HYBRID|CHAIN|FOUNDRY_IQ",
            "citations": [...],
            "pii_blocked": false
        }
    """
    try:
        data = request.get_json()

        if not data or 'message' not in data:
            return jsonify({"error": "Missing 'message' field"}), 400

        message = data['message']
        use_llm_routing = data.get('use_llm_routing', True)
        retrieval_mode = data.get('retrieval_mode', 'code-rag')

        if retrieval_mode == 'foundry-iq':
            # Use Foundry IQ Agent
            foundry_result = foundry_client.chat(message)

            # Format Foundry IQ citations to match code-rag format
            raw_citations = foundry_result.get("citations", [])
            formatted_citations = []
            for c in raw_citations:
                if isinstance(c, dict):
                    # Extract citation info from Foundry IQ annotation format
                    formatted_citations.append({
                        "source_type": "foundry_iq",
                        "identifier": c.get("url_citation", {}).get("title", c.get("text", "Unknown")),
                        "title": c.get("url_citation", {}).get("title", "Foundry IQ Knowledge Base"),
                        "content_preview": c.get("text", ""),
                        "score": 1.0
                    })

            response = {
                "answer": foundry_result.get("answer", "No answer available"),
                "route": "FOUNDRY_IQ",
                "reasoning": f"Using Foundry IQ agent ({foundry_result.get('agent', 'unknown')})",
                "citations": formatted_citations,
                "pii_blocked": False,
                "pii_warning": None,
                "sql_query": None
            }

            return jsonify(response)

        # Default: Use code-based RAG
        # Check if this will be a CHAIN query (long-running, needs progress updates)
        quick_route = router.quick_route(message)

        if quick_route == "CHAIN":
            # Stream progress for CHAIN queries using NDJSON
            # Use a queue to enable real-time streaming with threading
            progress_queue = queue.Queue()

            def progress_callback(progress):
                """Called by retriever to report progress - puts events in queue"""
                progress_queue.put({"type": "progress", **progress})

            def run_retriever():
                """Run retriever in background thread"""
                try:
                    result = retriever.answer(message, use_llm_routing=use_llm_routing,
                                             progress_callback=progress_callback)
                    # Signal completion with result
                    response = {
                        "type": "result",
                        "answer": result.answer,
                        "route": result.route,
                        "reasoning": result.reasoning,
                        "citations": [
                            {
                                "source_type": c.source_type,
                                "identifier": c.identifier,
                                "title": c.title,
                                "content_preview": c.content_preview,
                                "score": c.score
                            }
                            for c in result.citations
                        ],
                        "pii_blocked": result.pii_blocked,
                        "pii_warning": result.pii_warning,
                        "sql_query": result.sql_query
                    }
                    progress_queue.put(response)
                except Exception as e:
                    progress_queue.put({"type": "error", "message": str(e)})
                finally:
                    progress_queue.put(None)  # Sentinel to signal completion

            def generate_chain_response():
                """Generator that yields events from the queue"""
                # Start retriever in background thread
                thread = threading.Thread(target=run_retriever)
                thread.start()

                # Yield events as they come in
                while True:
                    try:
                        event = progress_queue.get(timeout=180)  # 3 minute timeout
                        if event is None:  # Sentinel - we're done
                            break
                        yield json.dumps(event) + "\n"
                    except queue.Empty:
                        # Timeout - return error
                        yield json.dumps({"type": "error", "message": "Query timeout"}) + "\n"
                        break

                thread.join(timeout=5)  # Wait for thread cleanup

            return Response(generate_chain_response(), mimetype='application/x-ndjson')

        # Non-CHAIN routes: return JSON as before
        result = retriever.answer(message, use_llm_routing=use_llm_routing)

        # Format response
        response = {
            "answer": result.answer,
            "route": result.route,
            "reasoning": result.reasoning,
            "citations": [
                {
                    "source_type": c.source_type,
                    "identifier": c.identifier,
                    "title": c.title,
                    "content_preview": c.content_preview,
                    "score": c.score
                }
                for c in result.citations
            ],
            "pii_blocked": result.pii_blocked,
            "pii_warning": result.pii_warning,
            "sql_query": result.sql_query
        }

        return jsonify(response)

    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/query', methods=['POST'])
def query():
    """
    Direct query endpoint with route specification.

    Request body:
        {
            "message": "Top 5 bond funds",
            "route": "SQL"  // Optional: SQL, SEMANTIC, RAPTOR, HYBRID, CHAIN
        }
    """
    try:
        data = request.get_json()

        if not data or 'message' not in data:
            return jsonify({"error": "Missing 'message' field"}), 400

        message = data['message']

        # Use heuristic routing for faster response
        result = retriever.answer(message, use_llm_routing=False)

        return jsonify({
            "answer": result.answer,
            "route": result.route,
            "citations": [c.to_dict() for c in result.citations],
            "pii_blocked": result.pii_blocked
        })

    except Exception as e:
        print(f"Error in query endpoint: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("=" * 60)
    print("FUND RAG API SERVER")
    print("=" * 60)
    print("Endpoints:")
    print("  GET  /health     - Health check")
    print("  POST /api/chat   - Chat with fund RAG")
    print("                     retrieval_mode: 'code-rag' | 'foundry-iq'")
    print("  POST /api/query  - Direct query")
    print("=" * 60)

    app.run(host='0.0.0.0', port=5001, debug=True)
