"use client";

import { useState, useEffect } from "react";
import { useTheme } from "next-themes";
import { Building2, Moon, Sun, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
  TooltipProvider,
} from "@/components/ui/tooltip";
import { DATA_PROVIDERS } from "@/data/seed";

export function Header() {
  const { theme, setTheme } = useTheme();
  // Prevent hydration mismatch by only showing dynamic content after mount
  const [mounted, setMounted] = useState(false);
  const [timestamp, setTimestamp] = useState<string | null>(null);

  useEffect(() => {
    setMounted(true);
    setTimestamp(new Date().toISOString().split("T")[0] + " 08:00 UTC");
  }, []);

  return (
    <header className="h-12 border-b border-border bg-surface-1 flex items-center justify-between px-4">
      {/* Left: Logo & Branding */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-gold/20 to-gold/5 border border-gold/20 flex items-center justify-center">
          <Building2 className="w-4 h-4 text-gold" />
        </div>
        <span className="font-semibold text-sm">Fund Intelligence</span>
      </div>

      {/* Center: Data Provenance Strip */}
      <div className="hidden md:flex items-center gap-4 text-xs text-muted-foreground">
        <span>
          Data as-of{" "}
          <span className="text-foreground font-medium">
            {timestamp ?? "Loading..."}
          </span>
        </span>
        <span className="w-px h-3 bg-border" />
        <span>Internal Use Only</span>
        <span className="w-px h-3 bg-border" />
        <span>
          Sources:{" "}
          {DATA_PROVIDERS.map((p) => p.name).join(", ")}
        </span>
      </div>

      {/* Right: Theme Toggle & User */}
      <div className="flex items-center gap-2">
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon-sm"
                onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
                aria-label="Toggle theme"
              >
                <Sun className="h-4 w-4 rotate-0 scale-100 transition-transform dark:-rotate-90 dark:scale-0" />
                <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-transform dark:rotate-0 dark:scale-100" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>{mounted ? (theme === "dark" ? "Ivory Ledger" : "Obsidian Ledger") : "Toggle theme"}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>

        <div className="w-px h-5 bg-border mx-1" />

        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="icon-sm" aria-label="Sign out">
                <LogOut className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>Sign out</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>
    </header>
  );
}
