import { z } from "zod";
import type { LookupFundingResult, FundingRound, Citation } from "@/types";

// Tool parameter schemas
export const LookupFundingParamsSchema = z.object({
  company: z.string().describe("The company name to look up funding for"),
  timeframe: z
    .enum(["all", "1y", "2y", "5y"])
    .optional()
    .default("all")
    .describe("Time period to search"),
  roundTypes: z
    .array(z.string())
    .optional()
    .describe("Filter by round types (e.g., Series A, Seed)"),
});

export type LookupFundingParams = z.infer<typeof LookupFundingParamsSchema>;

// Mock funding data
const MOCK_FUNDING_DATA: Record<string, LookupFundingResult> = {
  stripe: {
    summary: {
      company: "Stripe",
      totalRaised: 8700000000,
      roundCount: 18,
      lastRoundDate: "2023-03-15",
      lastRoundType: "Series I",
      latestValuation: 50000000000,
      topInvestors: [
        "Sequoia Capital",
        "Andreessen Horowitz",
        "General Catalyst",
        "GV",
      ],
    },
    rounds: [
      {
        id: "r1",
        company: "Stripe",
        roundType: "Series I",
        amount: 6500000000,
        date: "2023-03-15",
        investors: ["Sequoia Capital", "Andreessen Horowitz", "GIC"],
        valuation: 50000000000,
        source: "SEC N-PORT Q4 2024",
      },
      {
        id: "r2",
        company: "Stripe",
        roundType: "Series H",
        amount: 600000000,
        date: "2021-03-14",
        investors: ["Sequoia Capital", "Allianz X", "Fidelity"],
        valuation: 95000000000,
        source: "SEC N-PORT Q4 2024",
      },
      {
        id: "r3",
        company: "Stripe",
        roundType: "Series G",
        amount: 850000000,
        date: "2020-04-16",
        investors: ["Andreessen Horowitz", "General Catalyst", "GV"],
        valuation: 36000000000,
        source: "SEC N-PORT Q4 2024",
      },
    ],
    citations: [
      {
        id: 1,
        provider: "SEC EDGAR",
        dataset: "N-PORT Q4 2024",
        rowId: "NPORT-P/A:0001234567-24-000123",
        timestamp: "2024-12-15T08:30:00Z",
        confidence: 0.98,
      },
      {
        id: 2,
        provider: "SEC EDGAR",
        dataset: "N-PORT Q3 2024",
        rowId: "NPORT-P/A:0001234567-24-000089",
        timestamp: "2024-09-15T08:30:00Z",
        confidence: 0.95,
      },
    ],
  },
  openai: {
    summary: {
      company: "OpenAI",
      totalRaised: 11300000000,
      roundCount: 7,
      lastRoundDate: "2024-02-01",
      lastRoundType: "Venture Round",
      latestValuation: 86000000000,
      topInvestors: [
        "Microsoft",
        "Thrive Capital",
        "Khosla Ventures",
        "Tiger Global",
      ],
    },
    rounds: [
      {
        id: "r1",
        company: "OpenAI",
        roundType: "Venture Round",
        amount: 6600000000,
        date: "2024-02-01",
        investors: ["Microsoft", "Thrive Capital", "Khosla Ventures"],
        valuation: 86000000000,
        source: "SEC N-PORT Q4 2024",
      },
      {
        id: "r2",
        company: "OpenAI",
        roundType: "Venture Round",
        amount: 300000000,
        date: "2023-04-01",
        investors: ["Sequoia Capital", "Andreessen Horowitz", "Tiger Global"],
        valuation: 29000000000,
        source: "SEC N-PORT Q4 2024",
      },
    ],
    citations: [
      {
        id: 1,
        provider: "SEC EDGAR",
        dataset: "N-PORT Q4 2024",
        rowId: "NPORT-P/A:0009876543-24-000456",
        timestamp: "2024-12-10T14:22:00Z",
        confidence: 0.99,
      },
    ],
  },
  anthropic: {
    summary: {
      company: "Anthropic",
      totalRaised: 7600000000,
      roundCount: 5,
      lastRoundDate: "2024-01-15",
      lastRoundType: "Series D",
      latestValuation: 25000000000,
      topInvestors: ["Google", "Salesforce Ventures", "Spark Capital", "Sound Ventures"],
    },
    rounds: [
      {
        id: "r1",
        company: "Anthropic",
        roundType: "Series D",
        amount: 2000000000,
        date: "2024-01-15",
        investors: ["Google", "Salesforce Ventures"],
        valuation: 25000000000,
        source: "SEC N-PORT Q4 2024",
      },
      {
        id: "r2",
        company: "Anthropic",
        roundType: "Series C",
        amount: 4000000000,
        date: "2023-09-25",
        investors: ["Amazon", "Google", "Spark Capital"],
        valuation: 15000000000,
        source: "SEC N-PORT Q4 2024",
      },
    ],
    citations: [
      {
        id: 1,
        provider: "SEC EDGAR",
        dataset: "N-PORT Q4 2024",
        rowId: "NPORT-P/A:0005551234-24-000789",
        timestamp: "2024-12-12T10:15:00Z",
        confidence: 0.97,
      },
    ],
  },
};

/**
 * Mock implementation of lookup_funding tool
 * In production, this would query the PostgreSQL database
 */
export async function lookupFunding(
  params: LookupFundingParams
): Promise<LookupFundingResult | null> {
  const normalizedCompany = params.company.toLowerCase().replace(/\s+/g, "");

  // Simulate API latency
  await new Promise((resolve) => setTimeout(resolve, 500));

  const data = MOCK_FUNDING_DATA[normalizedCompany];

  if (!data) {
    return null;
  }

  // Filter by round types if specified
  let filteredRounds = data.rounds;
  if (params.roundTypes && params.roundTypes.length > 0) {
    filteredRounds = data.rounds.filter((r) =>
      params.roundTypes!.some(
        (type) => r.roundType.toLowerCase().includes(type.toLowerCase())
      )
    );
  }

  // Filter by timeframe
  if (params.timeframe !== "all") {
    const years = parseInt(params.timeframe);
    const cutoffDate = new Date();
    cutoffDate.setFullYear(cutoffDate.getFullYear() - years);
    filteredRounds = filteredRounds.filter(
      (r) => new Date(r.date) >= cutoffDate
    );
  }

  return {
    ...data,
    rounds: filteredRounds,
    summary: {
      ...data.summary,
      roundCount: filteredRounds.length,
      totalRaised: filteredRounds.reduce((sum, r) => sum + r.amount, 0),
    },
  };
}

/**
 * Generate a mock streaming response with tool calls
 */
export function generateMockResponse(
  query: string,
  fundingData: LookupFundingResult | null
): string {
  if (!fundingData) {
    return "I couldn't find any funding information for that company in our database. Please try searching for a different company or check the spelling.";
  }

  const { summary, rounds, citations } = fundingData;
  const citationRefs = citations.map((c) => `[${c.id}]`).join("");

  let response = `## ${summary.company} Funding Overview ${citationRefs}\n\n`;
  response += `**Total Raised:** $${(summary.totalRaised / 1e9).toFixed(1)}B across ${summary.roundCount} rounds\n\n`;

  if (summary.latestValuation) {
    response += `**Latest Valuation:** $${(summary.latestValuation / 1e9).toFixed(0)}B (${summary.lastRoundType}, ${summary.lastRoundDate})\n\n`;
  }

  response += `**Top Investors:** ${summary.topInvestors.join(", ")}\n\n`;

  if (rounds.length > 0) {
    response += `### Recent Funding Rounds\n\n`;
    response += `| Date | Round | Amount | Valuation |\n`;
    response += `|------|-------|--------|----------|\n`;

    rounds.slice(0, 5).forEach((round) => {
      const amount = round.amount >= 1e9
        ? `$${(round.amount / 1e9).toFixed(1)}B`
        : `$${(round.amount / 1e6).toFixed(0)}M`;
      const valuation = round.valuation
        ? `$${(round.valuation / 1e9).toFixed(0)}B`
        : "N/A";
      response += `| ${round.date} | ${round.roundType} | ${amount} | ${valuation} |\n`;
    });
  }

  return response;
}
