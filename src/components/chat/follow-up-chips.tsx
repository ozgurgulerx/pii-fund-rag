"use client";

import { motion } from "framer-motion";
import { Sparkles, Database, Compass, Layers, GitBranch, Globe } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { QueryType } from "@/data/seed";

interface FollowUpSuggestion {
  text: string;
  type: QueryType;
}

interface FollowUpChipsProps {
  suggestions: string[] | FollowUpSuggestion[];
  onSelect: (suggestion: string) => void;
  isVisible: boolean;
}

// Icon mapping for query types
const iconMap: Record<QueryType, React.ElementType> = {
  sql: Database,
  semantic: Compass,
  hybrid: Layers,
  chain: GitBranch,
  raptor: Globe,
};

// Color mapping for query types
const colorMap: Record<QueryType, { bg: string; text: string; border: string }> = {
  sql: { bg: "bg-blue-500/10", text: "text-blue-400", border: "border-blue-500/30" },
  semantic: { bg: "bg-purple-500/10", text: "text-purple-400", border: "border-purple-500/30" },
  hybrid: { bg: "bg-emerald-500/10", text: "text-emerald-400", border: "border-emerald-500/30" },
  chain: { bg: "bg-amber-500/10", text: "text-amber-400", border: "border-amber-500/30" },
  raptor: { bg: "bg-rose-500/10", text: "text-rose-400", border: "border-rose-500/30" },
};

// Infer query type from suggestion text (heuristic)
function inferQueryType(text: string): QueryType {
  const lowerText = text.toLowerCase();

  // RAPTOR keywords
  if (lowerText.includes("imf") || lowerText.includes("inflation outlook") ||
      lowerText.includes("economic") || lowerText.includes("growth forecast")) {
    return "raptor";
  }

  // Chain keywords
  if (lowerText.includes("position") || lowerText.includes("portfolio") ||
      lowerText.includes("if inflation") || lowerText.includes("how should")) {
    return "chain";
  }

  // Hybrid keywords
  if (lowerText.includes("rate environment") || lowerText.includes("given") ||
      lowerText.includes("considering") || lowerText.includes("based on")) {
    return "hybrid";
  }

  // Semantic keywords
  if (lowerText.includes("similar") || lowerText.includes("like") ||
      lowerText.includes("conservative") || lowerText.includes("aggressive") ||
      lowerText.includes("style") || lowerText.includes("income-focused")) {
    return "semantic";
  }

  // Default to SQL for data queries
  return "sql";
}

export function FollowUpChips({
  suggestions,
  onSelect,
  isVisible,
}: FollowUpChipsProps) {
  if (!isVisible || suggestions.length === 0) return null;

  // Normalize suggestions to include type information
  const normalizedSuggestions: FollowUpSuggestion[] = suggestions.map((s) => {
    if (typeof s === "string") {
      return { text: s, type: inferQueryType(s) };
    }
    return s;
  });

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 10 }}
      className="px-4 pb-4"
    >
      <div className="max-w-3xl mx-auto">
        <div className="flex items-center gap-2 mb-3">
          <Sparkles className="h-3 w-3 text-gold" />
          <span className="text-xs text-muted-foreground">
            Suggested follow-ups
          </span>
        </div>
        <div className="flex flex-wrap gap-2">
          {normalizedSuggestions.map((suggestion, index) => {
            const IconComponent = iconMap[suggestion.type];
            const colors = colorMap[suggestion.type];

            return (
              <motion.div
                key={suggestion.text}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.05 }}
              >
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onSelect(suggestion.text)}
                  className={`h-auto py-2 px-3 text-xs border ${colors.border} ${colors.bg} hover:${colors.bg} hover:border-opacity-50 transition-all group flex items-center gap-2`}
                >
                  <IconComponent className={`w-3 h-3 ${colors.text}`} />
                  <span>{suggestion.text}</span>
                </Button>
              </motion.div>
            );
          })}
        </div>
      </div>
    </motion.div>
  );
}
