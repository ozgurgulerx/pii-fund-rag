"use client";

import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronLeft,
  ChevronRight,
  Database,
  FileText,
  Clock,
  CheckCircle2,
  Copy,
  Download,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { cn, formatDateTime } from "@/lib/utils";
import type { Citation } from "@/types";

interface SourcesPanelProps {
  isCollapsed: boolean;
  onToggle: () => void;
  citations: Citation[];
  activeCitationId: number | null;
  onCitationClick: (id: number) => void;
}

export function SourcesPanel({
  isCollapsed,
  onToggle,
  citations,
  activeCitationId,
  onCitationClick,
}: SourcesPanelProps) {
  const handleCopyWithCitations = () => {
    // Mock implementation
    navigator.clipboard.writeText("Copied with citations...");
  };

  const handleExportPDF = () => {
    // Mock implementation
    console.log("Exporting PDF...");
  };

  const handleExportCSV = () => {
    // Mock implementation
    console.log("Exporting CSV...");
  };

  return (
    <motion.aside
      initial={false}
      animate={{ width: isCollapsed ? 56 : 320 }}
      transition={{ duration: 0.2, ease: "easeInOut" }}
      className="h-full border-l border-border bg-surface-1 flex flex-col relative"
    >
      {/* Toggle button */}
      <Button
        variant="ghost"
        size="icon-sm"
        onClick={onToggle}
        className="absolute -left-3 top-14 z-10 h-6 w-6 rounded-full border border-border bg-surface-2 shadow-subtle"
        aria-label={isCollapsed ? "Expand panel" : "Collapse panel"}
      >
        {isCollapsed ? (
          <ChevronLeft className="h-3 w-3" />
        ) : (
          <ChevronRight className="h-3 w-3" />
        )}
      </Button>

      {/* Header */}
      <div className="p-4 border-b border-border">
        <AnimatePresence mode="wait">
          {!isCollapsed ? (
            <motion.div
              key="expanded"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-3"
            >
              <div className="flex items-center justify-between">
                <h2 className="font-semibold text-sm">Sources & Provenance</h2>
                <Badge variant="gold" className="text-xs">
                  {citations.length} sources
                </Badge>
              </div>

              {/* Action buttons */}
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="flex-1 h-8 text-xs"
                  onClick={handleCopyWithCitations}
                >
                  <Copy className="h-3 w-3 mr-1" />
                  Copy
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="flex-1 h-8 text-xs"
                  onClick={handleExportPDF}
                >
                  <Download className="h-3 w-3 mr-1" />
                  PDF
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="flex-1 h-8 text-xs"
                  onClick={handleExportCSV}
                >
                  <FileText className="h-3 w-3 mr-1" />
                  CSV
                </Button>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="collapsed"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex justify-center"
            >
              <Database className="h-4 w-4 text-muted-foreground" />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Citations list */}
      <ScrollArea className="flex-1">
        <AnimatePresence>
          {!isCollapsed && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="p-4 space-y-3"
            >
              {citations.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground text-sm">
                  <Database className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p>No sources yet</p>
                  <p className="text-xs mt-1">
                    Sources will appear here as you chat
                  </p>
                </div>
              ) : (
                citations.map((citation) => (
                  <CitationCard
                    key={citation.id}
                    citation={citation}
                    isActive={citation.id === activeCitationId}
                    onClick={() => onCitationClick(citation.id)}
                  />
                ))
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Collapsed state */}
        {isCollapsed && citations.length > 0 && (
          <div className="p-2 flex flex-col items-center gap-2">
            {citations.map((citation) => (
              <Button
                key={citation.id}
                variant={citation.id === activeCitationId ? "secondary" : "ghost"}
                size="icon-sm"
                onClick={() => onCitationClick(citation.id)}
                className="w-8 h-8"
              >
                <span className="text-xs font-medium">{citation.id}</span>
              </Button>
            ))}
          </div>
        )}
      </ScrollArea>
    </motion.aside>
  );
}

function CitationCard({
  citation,
  isActive,
  onClick,
}: {
  citation: Citation;
  isActive: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full text-left p-3 rounded-lg border transition-all",
        isActive
          ? "border-gold/50 bg-gold/5 ring-1 ring-gold/20"
          : "border-border bg-surface-2 hover:bg-surface-3"
      )}
    >
      <div className="space-y-2">
        {/* Header */}
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="citation-chip">{citation.id}</span>
            <span className="font-medium text-sm">{citation.provider}</span>
          </div>
          <div className="flex items-center gap-1 text-xs text-emerald-500">
            <CheckCircle2 className="h-3 w-3" />
            <span>{Math.round(citation.confidence * 100)}%</span>
          </div>
        </div>

        {/* Dataset info */}
        <div className="text-xs text-muted-foreground space-y-1">
          <div className="flex items-center gap-1.5">
            <Database className="h-3 w-3" />
            <span>{citation.dataset}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <FileText className="h-3 w-3" />
            <span className="font-mono">{citation.rowId}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Clock className="h-3 w-3" />
            <span>{formatDateTime(citation.timestamp)}</span>
          </div>
        </div>

        {/* Excerpt */}
        {citation.excerpt && (
          <>
            <Separator className="my-2" />
            <p className="text-xs text-muted-foreground italic line-clamp-2">
              &ldquo;{citation.excerpt}&rdquo;
            </p>
          </>
        )}
      </div>
    </button>
  );
}
