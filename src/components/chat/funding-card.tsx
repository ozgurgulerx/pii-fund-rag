"use client";

import { motion } from "framer-motion";
import { TrendingUp, Building2, Calendar, Users } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatCurrency, formatCompactNumber } from "@/lib/utils";
import type { FundingSummary } from "@/types";

interface FundingCardProps {
  summary: FundingSummary;
}

export function FundingCard({ summary }: FundingCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card className="bg-gradient-to-br from-surface-2 to-surface-3 border-gold/20">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-gold/20 flex items-center justify-center">
                <Building2 className="h-4 w-4 text-gold" />
              </div>
              <CardTitle className="text-lg">{summary.company}</CardTitle>
            </div>
            <Badge variant="gold">
              {summary.roundCount} rounds
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Stats Grid */}
          <div className="grid grid-cols-2 gap-4">
            <StatItem
              icon={<TrendingUp className="h-4 w-4" />}
              label="Total Raised"
              value={formatCompactNumber(summary.totalRaised)}
            />
            {summary.latestValuation && (
              <StatItem
                icon={<TrendingUp className="h-4 w-4" />}
                label="Latest Valuation"
                value={formatCompactNumber(summary.latestValuation)}
              />
            )}
            <StatItem
              icon={<Calendar className="h-4 w-4" />}
              label="Last Round"
              value={summary.lastRoundType}
              subValue={summary.lastRoundDate}
            />
            <StatItem
              icon={<Users className="h-4 w-4" />}
              label="Top Investors"
              value={summary.topInvestors.length.toString()}
            />
          </div>

          {/* Top Investors */}
          <div className="pt-2 border-t border-border">
            <p className="text-xs text-muted-foreground mb-2">Key Investors</p>
            <div className="flex flex-wrap gap-1">
              {summary.topInvestors.slice(0, 4).map((investor) => (
                <Badge key={investor} variant="secondary" className="text-xs">
                  {investor}
                </Badge>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

function StatItem({
  icon,
  label,
  value,
  subValue,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  subValue?: string;
}) {
  return (
    <div className="space-y-1">
      <div className="flex items-center gap-1 text-muted-foreground">
        {icon}
        <span className="text-xs">{label}</span>
      </div>
      <p className="text-lg font-semibold">{value}</p>
      {subValue && (
        <p className="text-xs text-muted-foreground">{subValue}</p>
      )}
    </div>
  );
}
