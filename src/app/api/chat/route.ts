import { NextRequest } from "next/server";
import { z } from "zod";
import type { Citation } from "@/types";

const MessageSchema = z.object({
  role: z.enum(["user", "assistant", "system"]),
  content: z.string(),
});

const RequestSchema = z.object({
  messages: z.array(MessageSchema),
  retrievalMode: z.enum(["code-rag", "foundry-iq"]).optional().default("code-rag"),
});

// Python backend URL - BACKEND_URL for Azure deployment, PYTHON_API_URL for local dev
const PYTHON_API_URL = process.env.BACKEND_URL || process.env.PYTHON_API_URL || "http://localhost:5001";

// Streaming text encoder
const encoder = new TextEncoder();

function createSSEMessage(data: unknown): string {
  return `data: ${JSON.stringify(data)}\n\n`;
}

// Helper to stream result data to client (used for both JSON and NDJSON responses)
async function streamResultToClient(
  controller: ReadableStreamDefaultController,
  data: {
    answer: string;
    route: string;
    reasoning?: string;
    sql_query?: string;
    citations?: Array<{
      source_type: string;
      identifier: string;
      title: string;
      content_preview: string;
      score: number;
    }>;
    pii_blocked?: boolean;
    pii_warning?: string;
  }
) {
  // Check if PII was blocked
  if (data.pii_blocked) {
    controller.enqueue(
      encoder.encode(
        createSSEMessage({
          type: "pii_blocked",
          message: data.pii_warning || data.answer,
        })
      )
    );
  }

  // Stream the response word by word
  const responseText = data.answer;
  const words = responseText.split(" ");

  for (let i = 0; i < words.length; i++) {
    const word = words[i] + (i < words.length - 1 ? " " : "");
    controller.enqueue(
      encoder.encode(
        createSSEMessage({
          type: "text",
          content: word,
        })
      )
    );
    // Small delay for streaming effect
    await new Promise((resolve) => setTimeout(resolve, 5));
  }

  // Send route info
  controller.enqueue(
    encoder.encode(
      createSSEMessage({
        type: "metadata",
        route: data.route,
        reasoning: data.reasoning,
        sql_query: data.sql_query,
      })
    )
  );

  // Send citations if any
  if (data.citations && data.citations.length > 0) {
    const formattedCitations: Citation[] = data.citations.map(
      (c, idx) => ({
        id: idx + 1,
        provider: c.source_type,
        dataset: c.source_type === "SQL" ? "nport_funds.db" :
                 c.source_type === "SEMANTIC" ? "nport-funds-index" : "imf_raptor",
        rowId: c.identifier,
        timestamp: new Date().toISOString(),
        confidence: c.score || 0.9,
        excerpt: c.content_preview,
      })
    );

    controller.enqueue(
      encoder.encode(
        createSSEMessage({
          type: "citations",
          citations: formattedCitations,
        })
      )
    );
  }

  // Send completion signal
  const isVerified = data.route === "FOUNDRY_IQ" || (data.citations && data.citations.length > 0);
  controller.enqueue(
    encoder.encode(
      createSSEMessage({
        type: "done",
        isVerified,
      })
    )
  );
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const parsed = RequestSchema.safeParse(body);

    if (!parsed.success) {
      return new Response(
        JSON.stringify({ error: "Invalid request", details: parsed.error.issues }),
        { status: 400, headers: { "Content-Type": "application/json" } }
      );
    }

    const { messages, retrievalMode } = parsed.data;
    const lastUserMessage = messages.filter((m) => m.role === "user").pop();

    if (!lastUserMessage) {
      return new Response(
        JSON.stringify({ error: "No user message found" }),
        { status: 400, headers: { "Content-Type": "application/json" } }
      );
    }

    const query = lastUserMessage.content;

    // Create a streaming response
    const stream = new ReadableStream({
      async start(controller) {
        try {
          // Call Python backend
          controller.enqueue(
            encoder.encode(
              createSSEMessage({
                type: "tool_call",
                name: "fund_rag_query",
                arguments: { query },
              })
            )
          );

          // Call the Python API
          const response = await fetch(`${PYTHON_API_URL}/api/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              message: query,
              use_llm_routing: true,  // Use LLM routing for accurate path detection
              retrieval_mode: retrievalMode,
            }),
          });

          if (!response.ok) {
            throw new Error(`Python API error: ${response.status}`);
          }

          const contentType = response.headers.get("content-type") || "";

          // Handle NDJSON streaming response (CHAIN queries with progress)
          if (contentType.includes("application/x-ndjson")) {
            const reader = response.body?.getReader();
            if (!reader) {
              throw new Error("No response body reader");
            }

            const decoder = new TextDecoder();
            let buffer = "";

            while (true) {
              const { done, value } = await reader.read();
              if (done) break;

              buffer += decoder.decode(value, { stream: true });
              const lines = buffer.split("\n");
              buffer = lines.pop() || ""; // Keep incomplete line in buffer

              for (const line of lines) {
                if (!line.trim()) continue;

                try {
                  const event = JSON.parse(line);

                  if (event.type === "progress") {
                    // Forward progress event to frontend
                    controller.enqueue(
                      encoder.encode(
                        createSSEMessage({
                          type: "progress",
                          stage: event.stage,
                          message: event.message,
                        })
                      )
                    );
                  } else if (event.type === "result") {
                    // Handle final result same as regular JSON response
                    await streamResultToClient(controller, event);
                  }
                } catch (parseError) {
                  console.error("Error parsing NDJSON line:", line, parseError);
                }
              }
            }

            controller.close();
            return;
          }

          // Handle regular JSON response (non-CHAIN queries)
          const data = await response.json();
          await streamResultToClient(controller, data);
          controller.close();
        } catch (error) {
          console.error("Streaming error:", error);

          // Check if it's a connection error to Python backend
          const errorMessage = error instanceof Error ? error.message : "Unknown error";
          const isConnectionError = errorMessage.includes("ECONNREFUSED") ||
                                    errorMessage.includes("fetch failed");

          controller.enqueue(
            encoder.encode(
              createSSEMessage({
                type: "error",
                message: isConnectionError
                  ? "Backend server not running. Please start the Python API server (python api_server.py)"
                  : `Error: ${errorMessage}`,
              })
            )
          );
          controller.close();
        }
      },
    });

    return new Response(stream, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
      },
    });
  } catch (error) {
    console.error("Chat API error:", error);
    return new Response(
      JSON.stringify({ error: "Internal server error" }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }
}
