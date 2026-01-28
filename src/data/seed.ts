import type { Conversation, Message, Citation, WatchlistItem } from "@/types";

export const SAMPLE_CITATIONS: Citation[] = [
  {
    id: 1,
    provider: "SEC EDGAR",
    dataset: "N-PORT Q4 2024",
    rowId: "NPORT-P/A:0000102909-24-000892",
    timestamp: "2024-12-15T08:30:00Z",
    confidence: 0.98,
    excerpt: "Vanguard Total Bond Market Index Fund - Total Net Assets: $328.4B",
  },
  {
    id: 2,
    provider: "SEC EDGAR",
    dataset: "N-PORT Q4 2024",
    rowId: "NPORT-P/A:0000036405-24-001234",
    timestamp: "2024-12-10T14:22:00Z",
    confidence: 0.95,
    excerpt: "PIMCO Income Fund - MBS Holdings: 42.3% of portfolio, DV01: $8.2M",
  },
  {
    id: 3,
    provider: "IMF WEO",
    dataset: "World Economic Outlook Oct 2024",
    rowId: "IMF-WEO-2410-CH1",
    timestamp: "2024-10-22T00:00:00Z",
    confidence: 0.97,
    excerpt: "Global inflation expected to decline to 4.3% in 2025, supporting gradual rate cuts",
  },
  {
    id: 4,
    provider: "SEC EDGAR",
    dataset: "N-PORT Q4 2024",
    rowId: "NPORT-P/A:0000729218-24-000567",
    timestamp: "2024-12-12T10:15:00Z",
    confidence: 0.96,
    excerpt: "Fidelity Contrafund - NVIDIA Corp (CUSIP: 67066G104) - 4.2% of portfolio",
  },
];

export const SAMPLE_CONVERSATIONS: Conversation[] = [
  {
    id: "conv-1",
    title: "Bond Fund Analysis",
    createdAt: new Date("2024-12-20T10:30:00Z"),
    updatedAt: new Date("2024-12-20T10:35:00Z"),
    isSaved: true,
    messages: [
      {
        id: "msg-1",
        role: "user",
        content: "What are the top 5 largest bond funds by AUM?",
        createdAt: new Date("2024-12-20T10:30:00Z"),
      },
      {
        id: "msg-2",
        role: "assistant",
        content: `## Top 5 Bond Funds by AUM [1]

Based on the latest SEC N-PORT filings:

| Rank | Fund Name | Manager | Total Net Assets |
|------|-----------|---------|------------------|
| 1 | Vanguard Total Bond Market Index | Vanguard | $328.4B |
| 2 | PIMCO Income Fund | PIMCO | $142.7B |
| 3 | Vanguard Intermediate-Term Corporate | Vanguard | $89.2B |
| 4 | iShares Core U.S. Aggregate Bond | BlackRock | $85.1B |
| 5 | Metropolitan West Total Return Bond | MetWest | $78.4B |

**Key Insight:** Vanguard dominates the bond fund space with both the largest index fund and significant presence in corporate bonds.`,
        createdAt: new Date("2024-12-20T10:30:30Z"),
        citations: [SAMPLE_CITATIONS[0], SAMPLE_CITATIONS[1]],
        isVerified: true,
      },
      {
        id: "msg-3",
        role: "user",
        content: "What is PIMCO Income Fund's interest rate risk exposure?",
        createdAt: new Date("2024-12-20T10:32:00Z"),
      },
      {
        id: "msg-4",
        role: "assistant",
        content: `Based on the SEC N-PORT filings, PIMCO Income Fund has the following interest rate risk profile [2]:

### Duration Risk (DV01 by Tenor)
- **3-month:** $1.2M
- **1-year:** $2.8M
- **5-year:** $8.2M (largest exposure)
- **10-year:** $4.1M
- **30-year:** $1.9M

### Portfolio Composition
- **MBS Holdings:** 42.3% of portfolio
- **Corporate Bonds:** 28.1%
- **Government Securities:** 18.7%

**Key Insight:** The fund has concentrated duration risk in the 5-year tenor, making it sensitive to intermediate-term rate movements.`,
        createdAt: new Date("2024-12-20T10:32:30Z"),
        citations: [SAMPLE_CITATIONS[1]],
        isVerified: true,
      },
    ],
  },
  {
    id: "conv-2",
    title: "Macro + Fund Strategy",
    createdAt: new Date("2024-12-19T14:00:00Z"),
    updatedAt: new Date("2024-12-19T14:10:00Z"),
    isSaved: false,
    messages: [
      {
        id: "msg-5",
        role: "user",
        content: "Best bond funds given IMF's rate outlook?",
        createdAt: new Date("2024-12-19T14:00:00Z"),
      },
      {
        id: "msg-6",
        role: "assistant",
        content: `## Bond Fund Recommendations Based on IMF Outlook [2][3]

### IMF Economic Context
The IMF projects inflation to decline to 4.3% in 2025, supporting gradual rate cuts by major central banks. This creates a favorable environment for duration-sensitive assets.

### Recommended Funds

**For Income Seekers:**
- **PIMCO Income Fund** - High yield with active MBS management
- **Metropolitan West Total Return** - Diversified approach

**For Rate Sensitivity:**
- **Vanguard Long-Term Treasury** - Maximum duration benefit from rate cuts
- **iShares 20+ Year Treasury** - Pure long-duration exposure

**For Risk Management:**
- **Vanguard Short-Term Bond** - Lower volatility if rate path uncertain

**Key Insight:** With the IMF expecting disinflation, longer-duration funds should outperform, but investors should size positions based on their rate conviction.`,
        createdAt: new Date("2024-12-19T14:00:45Z"),
        citations: [SAMPLE_CITATIONS[1], SAMPLE_CITATIONS[2]],
        isVerified: true,
      },
    ],
  },
  {
    id: "conv-3",
    title: "Equity Fund Holdings",
    createdAt: new Date("2024-12-18T09:00:00Z"),
    updatedAt: new Date("2024-12-18T09:15:00Z"),
    isSaved: true,
    messages: [
      {
        id: "msg-7",
        role: "user",
        content: "Which funds hold NVIDIA stock?",
        createdAt: new Date("2024-12-18T09:00:00Z"),
      },
      {
        id: "msg-8",
        role: "assistant",
        content: `## Funds Holding NVIDIA (CUSIP: 67066G104) [4]

Based on N-PORT filings, here are the top funds by NVIDIA allocation:

| Fund | Manager | % of Portfolio | Value |
|------|---------|----------------|-------|
| Fidelity Contrafund | Fidelity | 4.2% | $5.8B |
| Vanguard Growth Index | Vanguard | 3.8% | $12.1B |
| T. Rowe Price Blue Chip | T. Rowe | 3.5% | $2.4B |
| American Funds Growth | Capital Group | 3.1% | $4.7B |
| Fidelity OTC Portfolio | Fidelity | 2.9% | $1.8B |

**Total NVIDIA Holdings:** $26.8B across top 5 funds

**Key Insight:** Fidelity Contrafund has the highest concentration, suggesting strong conviction in the AI/semiconductor thesis.`,
        createdAt: new Date("2024-12-18T09:00:30Z"),
        citations: [SAMPLE_CITATIONS[3]],
        isVerified: true,
      },
    ],
  },
];

export const SAMPLE_WATCHLIST: WatchlistItem[] = [
  {
    id: "w1",
    type: "company",
    name: "PIMCO Income Fund",
    addedAt: new Date("2024-12-15"),
  },
  {
    id: "w2",
    type: "company",
    name: "Vanguard Total Bond",
    addedAt: new Date("2024-12-18"),
  },
  {
    id: "w3",
    type: "investor",
    name: "Fidelity Contrafund",
    addedAt: new Date("2024-12-10"),
  },
  {
    id: "w4",
    type: "investor",
    name: "T. Rowe Price Growth",
    addedAt: new Date("2024-12-12"),
  },
];

// Legacy follow-up suggestions (string array for backwards compatibility)
export const FOLLOW_UP_SUGGESTIONS = [
  "Best bond funds given current rate environment?",
  "Which funds have highest NVIDIA exposure?",
  "Compare duration risk across top bond funds",
  "What does IMF say about emerging markets?",
];

// Query type definitions for the UI
export type QueryType = "sql" | "semantic" | "hybrid" | "chain" | "raptor";

// Enhanced follow-up suggestions with query type metadata
export interface FollowUpSuggestion {
  text: string;
  type: QueryType;
}

export const ENHANCED_FOLLOW_UP_SUGGESTIONS: FollowUpSuggestion[] = [
  { text: "Best bond funds given current rate environment?", type: "hybrid" },
  { text: "Which funds have highest NVIDIA exposure?", type: "sql" },
  { text: "Compare duration risk across top bond funds", type: "sql" },
  { text: "What does IMF say about emerging markets?", type: "raptor" },
  { text: "Conservative funds similar to Vanguard Total Bond", type: "semantic" },
  { text: "How should I position for Fed rate cuts?", type: "chain" },
];

export interface QueryCategory {
  id: QueryType;
  title: string;
  description: string;
  icon: string; // Lucide icon name
  color: string; // Tailwind color class
  examples: string[];
}

export const QUERY_CATEGORIES: QueryCategory[] = [
  {
    id: "sql",
    title: "SQL Queries",
    description: "Precise data lookups from SEC N-PORT filings",
    icon: "Database",
    color: "blue",
    examples: [
      "Top 10 funds by total net assets",
      "Which funds hold NVIDIA stock?",
      "Show me funds with DV01 exposure > $5M",
      "List all funds from Vanguard with AUM over $50B",
    ],
  },
  {
    id: "semantic",
    title: "Semantic Queries",
    description: "Find funds by investment style and similarity",
    icon: "Compass",
    color: "purple",
    examples: [
      "Conservative income-focused funds",
      "Funds similar to PIMCO Income Fund",
      "Growth-oriented equity funds",
      "Low-risk bond funds for retirement",
    ],
  },
  {
    id: "hybrid",
    title: "Hybrid Queries",
    description: "Combine fund data with macro economic context",
    icon: "Layers",
    color: "emerald",
    examples: [
      "Best bond funds given current rate environment",
      "Top funds considering inflation outlook",
      "High-yield funds positioned for soft landing",
      "Duration-sensitive funds for rate cut scenario",
    ],
  },
  {
    id: "chain",
    title: "Chain Queries",
    description: "Macro-driven multi-step fund selection",
    icon: "GitBranch",
    color: "amber",
    examples: [
      "How should I position my portfolio for IMF's growth forecast?",
      "Best funds if inflation rises above 3%",
      "Which funds benefit from emerging market recovery?",
      "Portfolio strategy based on Fed rate path",
    ],
  },
  {
    id: "raptor",
    title: "Economic Outlook",
    description: "IMF World Economic Outlook analysis",
    icon: "Globe",
    color: "rose",
    examples: [
      "What's the IMF's inflation outlook for 2025?",
      "Summarize IMF views on US growth",
      "What does IMF say about emerging markets?",
      "Global recession risk according to IMF",
    ],
  },
];

// Flattened list of all example queries with their types
export const ALL_QUERY_EXAMPLES = QUERY_CATEGORIES.flatMap((cat) =>
  cat.examples.map((example) => ({
    text: example,
    type: cat.id,
    color: cat.color,
  }))
);

export const DATA_PROVIDERS = [
  { name: "SEC EDGAR", type: "Primary" },
  { name: "N-PORT Filings", type: "Primary" },
  { name: "Form 13F", type: "Secondary" },
];

export function getDataAsOfTimestamp(): string {
  return new Date().toISOString().split("T")[0] + " 08:00 UTC";
}
