import { z } from "zod";

// PII Detection Types
export interface PiiEntity {
  text: string;
  category: string;
  offset: number;
  length: number;
  confidenceScore: number;
}

export interface PiiCheckResult {
  hasPii: boolean;
  entities: PiiEntity[];
  redactedText?: string;
}

// Chat Types
export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  createdAt: Date;
  citations?: Citation[];
  isVerified?: boolean;
  toolCalls?: ToolCall[];
}

export interface Citation {
  id: number;
  provider: string;
  dataset: string;
  rowId: string;
  timestamp: string;
  confidence: number;
  excerpt?: string;
}

export interface ToolCall {
  id: string;
  name: string;
  arguments: Record<string, unknown>;
  result?: unknown;
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: Date;
  updatedAt: Date;
  isSaved?: boolean;
}

// Funding Data Types
export const FundingRoundSchema = z.object({
  id: z.string(),
  company: z.string(),
  roundType: z.string(),
  amount: z.number(),
  date: z.string(),
  investors: z.array(z.string()),
  valuation: z.number().optional(),
  source: z.string(),
});

export type FundingRound = z.infer<typeof FundingRoundSchema>;

export const FundingSummarySchema = z.object({
  company: z.string(),
  totalRaised: z.number(),
  roundCount: z.number(),
  lastRoundDate: z.string(),
  lastRoundType: z.string(),
  latestValuation: z.number().optional(),
  topInvestors: z.array(z.string()),
});

export type FundingSummary = z.infer<typeof FundingSummarySchema>;

export const LookupFundingResultSchema = z.object({
  summary: FundingSummarySchema,
  rounds: z.array(FundingRoundSchema),
  citations: z.array(
    z.object({
      id: z.number(),
      provider: z.string(),
      dataset: z.string(),
      rowId: z.string(),
      timestamp: z.string(),
      confidence: z.number(),
    })
  ),
});

export type LookupFundingResult = z.infer<typeof LookupFundingResultSchema>;

// Watchlist Types
export interface WatchlistItem {
  id: string;
  type: "company" | "investor";
  name: string;
  addedAt: Date;
}

// Source Panel Types
export interface SourceReference {
  citationId: number;
  provider: string;
  dataset: string;
  rowId: string;
  timestamp: string;
  confidence: number;
  excerpt?: string;
  isActive?: boolean;
}

// API Response Types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}
