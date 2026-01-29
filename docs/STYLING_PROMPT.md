# Styling Prompt for Replicating Fund RAG POC Design

Copy and paste this prompt when setting up a new Next.js project with the same styling.

---

**PROMPT START**

Use the following styling system for this Next.js application. This is a premium financial/enterprise design with dual theme support.

## Tech Stack Required

```json
{
  "dependencies": {
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0",
    "@radix-ui/react-dialog": "^1.1.0",
    "@radix-ui/react-tooltip": "^1.1.0",
    "@radix-ui/react-scroll-area": "^1.2.0",
    "@radix-ui/react-switch": "^1.1.0",
    "@radix-ui/react-avatar": "^1.1.0",
    "@radix-ui/react-separator": "^1.1.0",
    "framer-motion": "^11.0.0",
    "next-themes": "^0.4.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.6.0",
    "lucide-react": "^0.468.0"
  }
}
```

## File Structure

```
src/
├── app/
│   ├── globals.css          # Theme variables + global styles
│   └── layout.tsx           # ThemeProvider wrapper
├── components/
│   ├── ui/                   # shadcn/ui components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── badge.tsx
│   │   ├── input.tsx
│   │   ├── textarea.tsx
│   │   ├── dialog.tsx
│   │   ├── tooltip.tsx
│   │   ├── scroll-area.tsx
│   │   ├── switch.tsx
│   │   ├── avatar.tsx
│   │   ├── separator.tsx
│   │   └── toast.tsx
│   └── providers/
│       └── theme-provider.tsx
├── lib/
│   └── utils.ts              # cn() utility function
├── tailwind.config.ts
└── postcss.config.mjs
```

## 1. Tailwind Config (`src/tailwind.config.ts`)

```typescript
import type { Config } from "tailwindcss";

export default {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        card: { DEFAULT: "hsl(var(--card))", foreground: "hsl(var(--card-foreground))" },
        popover: { DEFAULT: "hsl(var(--popover))", foreground: "hsl(var(--popover-foreground))" },
        primary: { DEFAULT: "hsl(var(--primary))", foreground: "hsl(var(--primary-foreground))" },
        secondary: { DEFAULT: "hsl(var(--secondary))", foreground: "hsl(var(--secondary-foreground))" },
        muted: { DEFAULT: "hsl(var(--muted))", foreground: "hsl(var(--muted-foreground))" },
        accent: { DEFAULT: "hsl(var(--accent))", foreground: "hsl(var(--accent-foreground))" },
        destructive: { DEFAULT: "hsl(var(--destructive))", foreground: "hsl(var(--destructive-foreground))" },
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        gold: { DEFAULT: "hsl(var(--gold))", foreground: "hsl(var(--gold-foreground))" },
        success: { DEFAULT: "hsl(var(--success))", foreground: "hsl(var(--success-foreground))" },
        warning: { DEFAULT: "hsl(var(--warning))", foreground: "hsl(var(--warning-foreground))" },
        surface: {
          1: "hsl(var(--surface-1))",
          2: "hsl(var(--surface-2))",
          3: "hsl(var(--surface-3))",
        },
      },
      borderRadius: {
        lg: "0.625rem",
        md: "calc(0.625rem - 2px)",
        sm: "calc(0.625rem - 4px)",
      },
      fontFamily: {
        sans: ["var(--font-sans)"],
        mono: ["var(--font-mono)"],
      },
      boxShadow: {
        subtle: "0 1px 2px 0 rgb(0 0 0 / 0.03)",
        elevated: "0 4px 6px -1px rgb(0 0 0 / 0.05), 0 2px 4px -2px rgb(0 0 0 / 0.03)",
        deep: "0 10px 15px -3px rgb(0 0 0 / 0.08), 0 4px 6px -4px rgb(0 0 0 / 0.04)",
      },
      keyframes: {
        "fade-in": { "0%": { opacity: "0" }, "100%": { opacity: "1" } },
        "slide-up": { "0%": { opacity: "0", transform: "translateY(10px)" }, "100%": { opacity: "1", transform: "translateY(0)" } },
        "pulse-subtle": { "0%, 100%": { opacity: "1" }, "50%": { opacity: "0.85" } },
      },
      animation: {
        "fade-in": "fade-in 0.2s ease-out",
        "slide-up": "slide-up 0.3s ease-out",
        "pulse-subtle": "pulse-subtle 2s ease-in-out infinite",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
} satisfies Config;
```

## 2. Global CSS (`src/app/globals.css`)

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    /* Light Theme - "Ivory Ledger" */
    --background: 40 20% 98%;
    --foreground: 220 20% 10%;
    --card: 40 15% 96%;
    --card-foreground: 220 20% 10%;
    --popover: 40 15% 96%;
    --popover-foreground: 220 20% 10%;
    --primary: 220 15% 20%;
    --primary-foreground: 40 20% 98%;
    --secondary: 40 10% 92%;
    --secondary-foreground: 220 15% 25%;
    --muted: 40 10% 92%;
    --muted-foreground: 220 10% 45%;
    --accent: 43 74% 49%;
    --accent-foreground: 220 20% 10%;
    --destructive: 0 72% 51%;
    --destructive-foreground: 0 0% 100%;
    --border: 40 15% 88%;
    --input: 40 15% 88%;
    --ring: 43 74% 49%;
    --gold: 43 74% 49%;
    --gold-foreground: 220 20% 10%;
    --success: 142 71% 45%;
    --success-foreground: 0 0% 100%;
    --warning: 38 92% 50%;
    --warning-foreground: 220 20% 10%;
    --surface-1: 40 15% 96%;
    --surface-2: 40 12% 94%;
    --surface-3: 40 10% 92%;
    --radius: 0.625rem;
  }

  .dark {
    /* Dark Theme - "Obsidian Ledger" */
    --background: 225 15% 8%;
    --foreground: 40 10% 92%;
    --card: 225 12% 11%;
    --card-foreground: 40 10% 92%;
    --popover: 225 12% 11%;
    --popover-foreground: 40 10% 92%;
    --primary: 43 60% 55%;
    --primary-foreground: 225 15% 8%;
    --secondary: 225 10% 18%;
    --secondary-foreground: 40 10% 85%;
    --muted: 225 10% 18%;
    --muted-foreground: 40 5% 55%;
    --accent: 43 60% 55%;
    --accent-foreground: 225 15% 8%;
    --destructive: 0 62% 50%;
    --destructive-foreground: 0 0% 100%;
    --border: 225 10% 18%;
    --input: 225 10% 18%;
    --ring: 43 60% 55%;
    --gold: 43 60% 55%;
    --gold-foreground: 225 15% 8%;
    --success: 142 71% 45%;
    --success-foreground: 0 0% 100%;
    --warning: 38 92% 50%;
    --warning-foreground: 225 15% 8%;
    --surface-1: 225 12% 11%;
    --surface-2: 225 11% 14%;
    --surface-3: 225 10% 17%;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground antialiased;
  }
}

/* Gold gradient text */
.text-gold-gradient {
  @apply bg-gradient-to-r from-amber-500 via-yellow-500 to-amber-600 bg-clip-text text-transparent;
}

/* Gold glow effect */
.glow-gold {
  box-shadow: 0 0 20px hsl(var(--gold) / 0.3);
}

/* Surface elevation classes */
.surface-1 { @apply bg-surface-1; }
.surface-2 { @apply bg-surface-2; }
.surface-3 { @apply bg-surface-3; }

/* Hairline border */
.border-hairline {
  border-width: 0.5px;
}
```

## 3. Utility Function (`src/lib/utils.ts`)

```typescript
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

## 4. Theme Provider (`src/components/providers/theme-provider.tsx`)

```typescript
"use client";

import * as React from "react";
import { ThemeProvider as NextThemesProvider } from "next-themes";
import { type ThemeProviderProps } from "next-themes";

export function ThemeProvider({ children, ...props }: ThemeProviderProps) {
  return <NextThemesProvider {...props}>{children}</NextThemesProvider>;
}
```

## 5. Button Component Example (`src/components/ui/button.tsx`)

```typescript
import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-[10px] text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground shadow-sm hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground shadow-sm hover:bg-destructive/90",
        outline: "border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground",
        secondary: "bg-secondary text-secondary-foreground shadow-sm hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
        gold: "bg-gold text-gold-foreground shadow-sm hover:bg-gold/90",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 rounded-md px-3 text-xs",
        lg: "h-10 rounded-md px-8",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: { variant: "default", size: "default" },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return <Comp className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />;
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };
```

## Design Principles

1. **Dual Themes**: Light "Ivory Ledger" (warm off-whites) and Dark "Obsidian Ledger" (deep blue-blacks)
2. **Gold Accents**: Primary accent color is gold (hsl 43 74% 49%) for premium feel
3. **Surface Elevation**: 3-level surface system (surface-1, surface-2, surface-3)
4. **10px Border Radius**: Consistent rounded corners (0.625rem)
5. **Subtle Shadows**: 3-tier shadow system (subtle, elevated, deep)
6. **CVA Pattern**: Use Class Variance Authority for component variants
7. **Radix Primitives**: Use Radix UI for accessible headless components
8. **Framer Motion**: Use for sophisticated animations (optional)

**PROMPT END**

---

## Reference Files in This Project

If you need to copy the exact styling files, reference these paths:

| File | Path |
|------|------|
| Global CSS | `src/app/globals.css` |
| Tailwind Config | `src/tailwind.config.ts` |
| PostCSS Config | `src/postcss.config.mjs` |
| Utils (cn function) | `src/lib/utils.ts` |
| Theme Provider | `src/components/providers/theme-provider.tsx` |
| UI Components | `src/components/ui/*.tsx` |
| Package.json | `src/package.json` |

## Quick Copy Command

To copy all styling files to another project:

```bash
# From the fund-rag-poc/src directory
cp app/globals.css /path/to/new-project/src/app/
cp tailwind.config.ts /path/to/new-project/src/
cp postcss.config.mjs /path/to/new-project/src/
cp lib/utils.ts /path/to/new-project/src/lib/
cp -r components/ui /path/to/new-project/src/components/
cp components/providers/theme-provider.tsx /path/to/new-project/src/components/providers/
```
