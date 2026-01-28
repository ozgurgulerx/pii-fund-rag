import type { Message, Conversation } from "@/types";
import { generateId } from "./utils";

/**
 * Create a new empty conversation
 */
export function createConversation(): Conversation {
  return {
    id: generateId(),
    title: "New Chat",
    messages: [],
    createdAt: new Date(),
    updatedAt: new Date(),
    isSaved: false,
  };
}

/**
 * Generate a title from the first user message
 */
export function generateConversationTitle(messages: Message[]): string {
  const firstUserMessage = messages.find((m) => m.role === "user");
  if (!firstUserMessage) return "New Chat";

  const content = firstUserMessage.content;
  if (content.length <= 40) return content;

  return content.substring(0, 40).trim() + "...";
}

/**
 * Parse streaming SSE response
 */
export interface StreamEvent {
  type: "text" | "tool_call" | "citations" | "done" | "error";
  content?: string;
  name?: string;
  arguments?: Record<string, unknown>;
  citations?: Array<{
    id: number;
    provider: string;
    dataset: string;
    rowId: string;
    timestamp: string;
    confidence: number;
  }>;
  isVerified?: boolean;
  message?: string;
}

export function parseSSELine(line: string): StreamEvent | null {
  if (!line.startsWith("data: ")) return null;

  try {
    return JSON.parse(line.slice(6)) as StreamEvent;
  } catch {
    return null;
  }
}

/**
 * Format message for API request
 */
export function formatMessagesForApi(
  messages: Message[]
): Array<{ role: string; content: string }> {
  return messages.map((m) => ({
    role: m.role,
    content: m.content,
  }));
}
