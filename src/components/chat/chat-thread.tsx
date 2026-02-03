"use client";

import { useRef, useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Loader2,
  Sparkles,
  Database,
  Compass,
  Layers,
  GitBranch,
  Globe,
  ChevronRight,
  ArrowRight,
  CheckCircle,
} from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Message } from "./message";
import { QUERY_CATEGORIES, type QueryType } from "@/data/seed";
import type { Message as MessageType } from "@/types";

interface ChatThreadProps {
  messages: MessageType[];
  isLoading: boolean;
  streamingContent?: string;
  queryProgress?: { stage: string; message: string }[];
  onCitationClick?: (id: number) => void;
  activeCitationId?: number | null;
  onSendMessage?: (message: string) => void;
}

// Icon mapping for query categories
const iconMap: Record<string, React.ElementType> = {
  Database,
  Compass,
  Layers,
  GitBranch,
  Globe,
};

// Color mapping for query categories
const colorMap: Record<string, { bg: string; border: string; text: string; hover: string; badge: string }> = {
  blue: {
    bg: "bg-blue-500/10",
    border: "border-blue-500/30",
    text: "text-blue-400",
    hover: "hover:bg-blue-500/20 hover:border-blue-500/50",
    badge: "bg-blue-500/20 text-blue-300",
  },
  purple: {
    bg: "bg-purple-500/10",
    border: "border-purple-500/30",
    text: "text-purple-400",
    hover: "hover:bg-purple-500/20 hover:border-purple-500/50",
    badge: "bg-purple-500/20 text-purple-300",
  },
  emerald: {
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/30",
    text: "text-emerald-400",
    hover: "hover:bg-emerald-500/20 hover:border-emerald-500/50",
    badge: "bg-emerald-500/20 text-emerald-300",
  },
  amber: {
    bg: "bg-amber-500/10",
    border: "border-amber-500/30",
    text: "text-amber-400",
    hover: "hover:bg-amber-500/20 hover:border-amber-500/50",
    badge: "bg-amber-500/20 text-amber-300",
  },
  rose: {
    bg: "bg-rose-500/10",
    border: "border-rose-500/30",
    text: "text-rose-400",
    hover: "hover:bg-rose-500/20 hover:border-rose-500/50",
    badge: "bg-rose-500/20 text-rose-300",
  },
};

export function ChatThread({
  messages,
  isLoading,
  streamingContent,
  queryProgress = [],
  onCitationClick,
  activeCitationId,
  onSendMessage,
}: ChatThreadProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    // Use scrollIntoView for more reliable scrolling
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContent]);

  return (
    <ScrollArea className="flex-1 min-h-0" ref={scrollRef}>
      <div className="max-w-4xl mx-auto px-4 py-6">
        {messages.length === 0 ? (
          <EmptyState onSendMessage={onSendMessage} />
        ) : (
          <AnimatePresence mode="popLayout">
            {messages.map((message) => (
              <Message
                key={message.id}
                message={message}
                onCitationClick={onCitationClick}
                activeCitationId={activeCitationId}
              />
            ))}

            {/* Streaming response */}
            {isLoading && streamingContent && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex gap-3 py-4"
              >
                <div className="h-8 w-8 rounded-full bg-surface-3 flex items-center justify-center">
                  <Sparkles className="h-4 w-4 text-gold animate-pulse" />
                </div>
                <div className="flex-1 max-w-[85%]">
                  <div className="rounded-xl px-4 py-3 bg-surface-2 border border-border">
                    <div className="markdown-content text-sm">
                      {streamingContent}
                      <span className="inline-block w-2 h-4 bg-gold/50 animate-pulse ml-0.5" />
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {/* Loading indicator without content */}
            {isLoading && !streamingContent && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex gap-3 py-4"
              >
                <div className="h-8 w-8 rounded-full bg-surface-3 flex items-center justify-center">
                  <Loader2 className="h-4 w-4 text-muted-foreground animate-spin" />
                </div>
                <div className="flex-1 max-w-[85%]">
                  <div className="rounded-xl px-4 py-3 bg-surface-2 border border-border">
                    {queryProgress.length > 0 ? (
                      /* Progress steps for CHAIN queries */
                      <div className="flex flex-col gap-2">
                        {queryProgress.map((p, i) => (
                          <motion.div
                            key={`${p.stage}-${i}`}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ duration: 0.2 }}
                            className="flex items-center gap-2 text-sm"
                          >
                            {i === queryProgress.length - 1 ? (
                              <Loader2 className="h-4 w-4 text-amber-500 animate-spin flex-shrink-0" />
                            ) : (
                              <CheckCircle className="h-4 w-4 text-green-500 flex-shrink-0" />
                            )}
                            <span className={i === queryProgress.length - 1 ? "text-foreground" : "text-muted-foreground"}>
                              {p.message}
                            </span>
                          </motion.div>
                        ))}
                      </div>
                    ) : (
                      /* Default loading indicator */
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <span>Analyzing fund data</span>
                        <span className="flex gap-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-gold animate-bounce" style={{ animationDelay: "0ms" }} />
                          <span className="w-1.5 h-1.5 rounded-full bg-gold animate-bounce" style={{ animationDelay: "150ms" }} />
                          <span className="w-1.5 h-1.5 rounded-full bg-gold animate-bounce" style={{ animationDelay: "300ms" }} />
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        )}

        {/* Scroll anchor */}
        <div ref={bottomRef} className="h-1" />
      </div>
    </ScrollArea>
  );
}

interface EmptyStateProps {
  onSendMessage?: (message: string) => void;
}

function EmptyState({ onSendMessage }: EmptyStateProps) {
  const [expandedCategory, setExpandedCategory] = useState<QueryType | null>(null);

  const handleExampleClick = (example: string) => {
    if (onSendMessage) {
      onSendMessage(example);
    }
  };

  const toggleCategory = (categoryId: QueryType) => {
    setExpandedCategory((prev) => (prev === categoryId ? null : categoryId));
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="flex flex-col items-center py-8"
    >
      {/* Header */}
      <div className="text-center mb-8">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-gold/20 to-gold/5 border border-gold/20 flex items-center justify-center mb-4 mx-auto">
          <Sparkles className="w-8 h-8 text-gold" />
        </div>
        <h2 className="text-2xl font-semibold mb-2">Fund Intelligence</h2>
        <p className="text-muted-foreground text-sm max-w-lg">
          Query mutual fund data from SEC N-PORT filings combined with IMF economic outlook.
          Choose a query type below or ask anything.
        </p>
      </div>

      {/* Query Categories Grid */}
      <div className="w-full max-w-3xl space-y-3">
        {QUERY_CATEGORIES.map((category, index) => {
          const IconComponent = iconMap[category.icon] || Database;
          const colors = colorMap[category.color] || colorMap.blue;
          const isExpanded = expandedCategory === category.id;

          return (
            <motion.div
              key={category.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.08, duration: 0.4 }}
            >
              {/* Category Header - Clickable */}
              <button
                onClick={() => toggleCategory(category.id)}
                className={`w-full text-left p-4 rounded-xl border ${colors.border} ${colors.bg} ${colors.hover} transition-all group`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${colors.bg} border ${colors.border}`}>
                      <IconComponent className={`w-5 h-5 ${colors.text}`} />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className={`font-semibold ${colors.text}`}>
                          {category.title}
                        </h3>
                        <span className={`text-[10px] px-2 py-0.5 rounded-full ${colors.badge} uppercase tracking-wider`}>
                          {category.id}
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {category.description}
                      </p>
                    </div>
                  </div>
                  <motion.div
                    animate={{ rotate: isExpanded ? 90 : 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    <ChevronRight className={`w-5 h-5 ${colors.text} opacity-50`} />
                  </motion.div>
                </div>
              </button>

              {/* Expanded Examples */}
              <AnimatePresence>
                {isExpanded && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.2 }}
                    className="overflow-hidden"
                  >
                    <div className="pt-2 pl-4 space-y-2">
                      {category.examples.map((example, exIndex) => (
                        <motion.button
                          key={example}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: exIndex * 0.05 }}
                          onClick={() => handleExampleClick(example)}
                          className={`w-full text-left p-3 rounded-lg border border-border/50 bg-surface-1 hover:bg-surface-2 hover:border-${category.color}-500/30 transition-all group flex items-center justify-between`}
                        >
                          <span className="text-sm text-foreground/80 group-hover:text-foreground">
                            {example}
                          </span>
                          <ArrowRight className={`w-4 h-4 ${colors.text} opacity-0 group-hover:opacity-100 transition-opacity`} />
                        </motion.button>
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          );
        })}
      </div>

      {/* Quick Start - Popular Queries */}
      <div className="mt-8 w-full max-w-3xl">
        <div className="flex items-center gap-2 mb-3">
          <Sparkles className="w-4 h-4 text-gold" />
          <span className="text-sm font-medium text-muted-foreground">Popular queries</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {[
            { text: "Top 10 bond funds by AUM", color: "blue" },
            { text: "Conservative income funds", color: "purple" },
            { text: "Best funds for rate cuts", color: "emerald" },
            { text: "IMF inflation outlook 2025", color: "rose" },
          ].map((query, index) => {
            const colors = colorMap[query.color];
            return (
              <motion.button
                key={query.text}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.5 + index * 0.05 }}
                onClick={() => handleExampleClick(query.text)}
                className={`px-3 py-2 rounded-lg text-sm border ${colors.border} ${colors.bg} ${colors.hover} ${colors.text} transition-all`}
              >
                {query.text}
              </motion.button>
            );
          })}
        </div>
      </div>
    </motion.div>
  );
}
