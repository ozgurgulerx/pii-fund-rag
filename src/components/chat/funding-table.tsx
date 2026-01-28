"use client";

import { motion } from "framer-motion";
import { ArrowUpRight, ExternalLink } from "lucide-react";
import { formatCurrency, formatCompactNumber, formatDate } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import type { FundingRound } from "@/types";

interface FundingTableProps {
  rounds: FundingRound[];
  citations?: number[];
}

export function FundingTable({ rounds, citations = [] }: FundingTableProps) {
  if (rounds.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="overflow-hidden rounded-lg border border-border"
    >
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-surface-2 border-b border-border">
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                Date
              </th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                Round
              </th>
              <th className="px-4 py-3 text-right font-medium text-muted-foreground">
                Amount
              </th>
              <th className="px-4 py-3 text-right font-medium text-muted-foreground">
                Valuation
              </th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                Lead Investors
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {rounds.map((round, index) => (
              <motion.tr
                key={round.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                className="bg-card hover:bg-surface-2 transition-colors"
              >
                <td className="px-4 py-3 text-muted-foreground">
                  {formatDate(round.date)}
                </td>
                <td className="px-4 py-3">
                  <Badge variant="outline" className="font-medium">
                    {round.roundType}
                  </Badge>
                </td>
                <td className="px-4 py-3 text-right font-medium tabular-nums">
                  <span className="text-gold">
                    ${formatCompactNumber(round.amount)}
                  </span>
                </td>
                <td className="px-4 py-3 text-right text-muted-foreground tabular-nums">
                  {round.valuation
                    ? `$${formatCompactNumber(round.valuation)}`
                    : "—"}
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {round.investors.slice(0, 3).map((investor) => (
                      <span
                        key={investor}
                        className="text-xs text-muted-foreground"
                      >
                        {investor}
                        {round.investors.indexOf(investor) < 2 &&
                          round.investors.indexOf(investor) <
                            round.investors.length - 1 && ", "}
                      </span>
                    ))}
                    {round.investors.length > 3 && (
                      <span className="text-xs text-muted-foreground">
                        +{round.investors.length - 3} more
                      </span>
                    )}
                  </div>
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Source footer */}
      <div className="px-4 py-2 bg-surface-2 border-t border-border flex items-center justify-between text-xs text-muted-foreground">
        <span>Source: SEC N-PORT Filings</span>
        {citations.length > 0 && (
          <span className="flex items-center gap-1">
            <ExternalLink className="h-3 w-3" />
            Citations: {citations.map((c) => `[${c}]`).join(" ")}
          </span>
        )}
      </div>
    </motion.div>
  );
}
