"use client";

import { motion } from "framer-motion";
import { formatCompactNumber, formatDate } from "@/lib/utils";
import type { FundingRound } from "@/types";

interface TimelineChartProps {
  rounds: FundingRound[];
  height?: number;
}

export function TimelineChart({ rounds, height = 120 }: TimelineChartProps) {
  if (rounds.length === 0) return null;

  // Sort rounds by date
  const sortedRounds = [...rounds].sort(
    (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
  );

  // Calculate max amount for scaling
  const maxAmount = Math.max(...sortedRounds.map((r) => r.amount));

  // Chart dimensions
  const padding = { top: 20, right: 20, bottom: 40, left: 50 };
  const chartWidth = 400;
  const chartHeight = height;
  const innerWidth = chartWidth - padding.left - padding.right;
  const innerHeight = chartHeight - padding.top - padding.bottom;

  // Calculate positions
  const xStep = innerWidth / (sortedRounds.length - 1 || 1);
  const points = sortedRounds.map((round, index) => ({
    x: padding.left + index * xStep,
    y: padding.top + innerHeight - (round.amount / maxAmount) * innerHeight,
    round,
  }));

  // Create path for line
  const linePath = points
    .map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`)
    .join(" ");

  // Create path for area fill
  const areaPath = `${linePath} L ${points[points.length - 1].x} ${padding.top + innerHeight} L ${points[0].x} ${padding.top + innerHeight} Z`;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="rounded-lg border border-border bg-surface-2 p-4"
    >
      <h4 className="text-sm font-medium mb-3">Funding Timeline</h4>
      <svg
        viewBox={`0 0 ${chartWidth} ${chartHeight}`}
        className="w-full h-auto"
        style={{ maxHeight: height }}
      >
        <defs>
          <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="hsl(43 60% 45%)" stopOpacity="0.3" />
            <stop offset="100%" stopColor="hsl(43 60% 45%)" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* Grid lines */}
        {[0, 0.25, 0.5, 0.75, 1].map((ratio) => (
          <g key={ratio}>
            <line
              x1={padding.left}
              y1={padding.top + innerHeight * (1 - ratio)}
              x2={chartWidth - padding.right}
              y2={padding.top + innerHeight * (1 - ratio)}
              stroke="hsl(var(--border))"
              strokeWidth="1"
              strokeDasharray="4 4"
              opacity="0.5"
            />
            <text
              x={padding.left - 8}
              y={padding.top + innerHeight * (1 - ratio) + 4}
              textAnchor="end"
              className="fill-muted-foreground text-[10px]"
            >
              ${formatCompactNumber(maxAmount * ratio)}
            </text>
          </g>
        ))}

        {/* Area fill */}
        <motion.path
          d={areaPath}
          fill="url(#areaGradient)"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        />

        {/* Line */}
        <motion.path
          d={linePath}
          fill="none"
          stroke="hsl(43 60% 45%)"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 1, ease: "easeOut" }}
        />

        {/* Points */}
        {points.map((point, index) => (
          <motion.g
            key={point.round.id}
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.5 + index * 0.1 }}
          >
            <circle
              cx={point.x}
              cy={point.y}
              r="6"
              fill="hsl(var(--background))"
              stroke="hsl(43 60% 45%)"
              strokeWidth="2"
            />
            <circle
              cx={point.x}
              cy={point.y}
              r="3"
              fill="hsl(43 60% 45%)"
            />
            {/* Date label */}
            <text
              x={point.x}
              y={chartHeight - 8}
              textAnchor="middle"
              className="fill-muted-foreground text-[9px]"
            >
              {new Date(point.round.date).getFullYear()}
            </text>
          </motion.g>
        ))}
      </svg>
    </motion.div>
  );
}
