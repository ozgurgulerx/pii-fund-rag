import { AlertTriangle, Mail } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-border bg-surface-1 py-2 px-4">
      <div className="flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-muted-foreground">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-3 h-3" />
          <span>
            Not investment advice. Data provided for informational purposes only.
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="font-medium">Built by Innovation Hub Istanbul</span>
          <span className="hidden sm:inline">|</span>
          <a
            href="mailto:ozgurguler@microsoft.com"
            className="flex items-center gap-1 hover:text-foreground transition-colors"
          >
            <Mail className="w-3 h-3" />
            <span>Ozgur Guler</span>
          </a>
        </div>
      </div>
    </footer>
  );
}
