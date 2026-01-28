"use client";

// Build timestamp: 2026-01-28T12:10:00Z - forces chunk regeneration
import { useState, useCallback } from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { SourcesPanel } from "@/components/layout/sources-panel";
import { ChatThread } from "@/components/chat/chat-thread";
import { MessageComposer } from "@/components/chat/message-composer";
import { FollowUpChips } from "@/components/chat/follow-up-chips";
import { ToggleGroup } from "@/components/ui/switch";
import { generateId } from "@/lib/utils";
import {
  SAMPLE_CONVERSATIONS,
  SAMPLE_CITATIONS,
  ENHANCED_FOLLOW_UP_SUGGESTIONS,
} from "@/data/seed";
import type { Message, Citation, Conversation } from "@/types";

type RetrievalMode = "code-rag" | "foundry-iq";

export default function ChatPage() {
  // Panel state
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [sourcesPanelCollapsed, setSourcesPanelCollapsed] = useState(false);

  // Retrieval mode state
  const [retrievalMode, setRetrievalMode] = useState<RetrievalMode>("code-rag");

  // Chat state
  const [activeConversationId, setActiveConversationId] = useState<string | null>(
    SAMPLE_CONVERSATIONS[0]?.id || null
  );
  const [messages, setMessages] = useState<Message[]>(
    SAMPLE_CONVERSATIONS[0]?.messages || []
  );
  const [citations, setCitations] = useState<Citation[]>(
    SAMPLE_CONVERSATIONS[0]?.messages
      .flatMap((m) => m.citations || [])
      .filter((c, i, arr) => arr.findIndex((x) => x.id === c.id) === i) || []
  );
  const [activeCitationId, setActiveCitationId] = useState<number | null>(null);

  // Streaming state
  const [isLoading, setIsLoading] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");

  // Show follow-ups after assistant response
  const [showFollowUps, setShowFollowUps] = useState(true);

  const handleNewChat = useCallback(() => {
    setActiveConversationId(null);
    setMessages([]);
    setCitations([]);
    setActiveCitationId(null);
    setShowFollowUps(false);
    setStreamingContent("");
  }, []);

  const handleSelectConversation = useCallback((id: string) => {
    const conversation = SAMPLE_CONVERSATIONS.find((c) => c.id === id);
    if (conversation) {
      setActiveConversationId(id);
      setMessages(conversation.messages);
      setCitations(
        conversation.messages
          .flatMap((m) => m.citations || [])
          .filter((c, i, arr) => arr.findIndex((x) => x.id === c.id) === i)
      );
      setActiveCitationId(null);
      setShowFollowUps(true);
    }
  }, []);

  const handleCitationClick = useCallback((id: number) => {
    setActiveCitationId((prev) => (prev === id ? null : id));
  }, []);

  const handleSendMessage = useCallback(async (content: string) => {
    // Add user message
    const userMessage: Message = {
      id: generateId(),
      role: "user",
      content,
      createdAt: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setStreamingContent("");
    setShowFollowUps(false);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: [...messages, userMessage].map((m) => ({
            role: m.role,
            content: m.content,
          })),
          retrievalMode: retrievalMode,
        }),
      });

      if (!response.ok) {
        throw new Error("Chat request failed");
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error("No response body");

      const decoder = new TextDecoder();
      let fullContent = "";
      let newCitations: Citation[] = [];
      let isVerified = false;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));

              switch (data.type) {
                case "text":
                  fullContent += data.content;
                  setStreamingContent(fullContent);
                  break;
                case "citations":
                  newCitations = data.citations;
                  break;
                case "done":
                  isVerified = data.isVerified;
                  break;
                case "error":
                  throw new Error(data.message);
              }
            } catch (e) {
              // Re-throw if it's an intentional error (not a JSON parse error)
              if (e instanceof Error && !e.message.includes("JSON")) {
                throw e;
              }
              // Ignore JSON parse errors for incomplete chunks
            }
          }
        }
      }

      // Add assistant message
      const assistantMessage: Message = {
        id: generateId(),
        role: "assistant",
        content: fullContent,
        createdAt: new Date(),
        citations: newCitations,
        isVerified,
      };

      setMessages((prev) => [...prev, assistantMessage]);

      // Update citations panel - use rowId for deduplication, assign sequential display IDs
      if (newCitations.length > 0) {
        setCitations((prev) => {
          const existingRowIds = new Set(prev.map((c) => c.rowId));
          const uniqueNew = newCitations
            .filter((c) => !existingRowIds.has(c.rowId))
            .map((c, idx) => ({
              ...c,
              id: prev.length + idx + 1,  // Assign sequential ID based on current length
            }));
          return [...prev, ...uniqueNew];
        });
      }

      setShowFollowUps(true);
    } catch (error) {
      console.error("Chat error:", error);
      // Add error message
      const errorMessage: Message = {
        id: generateId(),
        role: "assistant",
        content: "I apologize, but I encountered an error processing your request. Please try again.",
        createdAt: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setStreamingContent("");
    }
  }, [messages, retrievalMode]);

  const handleFollowUpSelect = useCallback(
    (suggestion: string) => {
      handleSendMessage(suggestion);
    },
    [handleSendMessage]
  );

  return (
    <div className="flex h-full">
      {/* Left Sidebar */}
      <Sidebar
        isCollapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed((prev) => !prev)}
        onSelectConversation={handleSelectConversation}
        activeConversationId={activeConversationId ?? undefined}
        onNewChat={handleNewChat}
      />

      {/* Center: Chat */}
      <div className="flex-1 flex flex-col min-w-0 min-h-0 bg-background relative">
        {/* Subtle grid pattern */}
        <div className="absolute inset-0 grid-pattern opacity-50 pointer-events-none" />

        <div className="relative flex-1 flex flex-col min-h-0 z-10">
          {/* Retrieval Mode Toggle */}
          <div className="flex items-center justify-center py-2 border-b border-border bg-surface-1/50">
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">Retrieval:</span>
              <ToggleGroup
                value={retrievalMode}
                onValueChange={(v) => setRetrievalMode(v as RetrievalMode)}
                options={[
                  { value: "code-rag", label: "Code-based RAG" },
                  { value: "foundry-iq", label: "Foundry IQ" },
                ]}
              />
            </div>
          </div>

          <ChatThread
            messages={messages}
            isLoading={isLoading}
            streamingContent={streamingContent}
            onCitationClick={handleCitationClick}
            activeCitationId={activeCitationId}
            onSendMessage={handleSendMessage}
          />

          <FollowUpChips
            suggestions={ENHANCED_FOLLOW_UP_SUGGESTIONS}
            onSelect={handleFollowUpSelect}
            isVisible={showFollowUps && !isLoading && messages.length > 0}
          />

          <MessageComposer
            onSubmit={handleSendMessage}
            isLoading={isLoading}
          />
        </div>
      </div>

      {/* Right Panel: Sources */}
      <SourcesPanel
        isCollapsed={sourcesPanelCollapsed}
        onToggle={() => setSourcesPanelCollapsed((prev) => !prev)}
        citations={citations}
        activeCitationId={activeCitationId}
        onCitationClick={handleCitationClick}
      />
    </div>
  );
}
