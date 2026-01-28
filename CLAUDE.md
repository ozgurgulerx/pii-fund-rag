# Fund RAG POC - Development Guidelines

## Project Overview
Enterprise-grade RAG Q&A chatbot for mutual fund/ETF data using SEC N-PORT filings with PII protection.

## Production Architecture (Azure)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AZURE DEPLOYMENT                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────┐        ┌──────────────────────────────────────┐   │
│  │   Azure App Service  │        │     Azure Kubernetes Service (AKS)    │   │
│  │   (Frontend)         │        │     (Backend)                         │   │
│  │                      │        │                                       │   │
│  │  fundrag-frontend    │ ───────▶  fund-rag-backend (Flask)            │   │
│  │  .azurewebsites.net  │  API   │  - /api/chat (RAG queries)           │   │
│  │                      │        │  - /health                            │   │
│  │  Next.js 15 + React  │        │                                       │   │
│  │  - PII UI animations │        │  aks-fund-rag (1-2 nodes autoscale)  │   │
│  │  - Chat interface    │        │  rg-fund-rag / westeurope             │   │
│  └──────────┬───────────┘        └──────────────┬───────────────────────┘   │
│             │                                    │                          │
│             │ PII Check                          │ SQL Queries              │
│             ▼                                    ▼                          │
│  ┌──────────────────────┐        ┌──────────────────────────────────────┐   │
│  │  Azure Container     │        │    Azure PostgreSQL (Private EP)     │   │
│  │  Instances (PII)     │        │                                       │   │
│  │                      │        │  aistartupstr.postgres.database.     │   │
│  │  pii-ozguler.eastus  │        │  azure.com                           │   │
│  │  .azurecontainer.io  │        │                                       │   │
│  │  :5000               │        │  Database: fundrag                    │   │
│  │                      │        │  Schema: nport_funds                  │   │
│  │  Azure Language PII  │        │  - 250 funds, 490K holdings          │   │
│  │  Detection Service   │        │  - 15 tables from SEC N-PORT          │   │
│  └──────────────────────┘        └──────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────┐        ┌──────────────────────────────────────┐   │
│  │  Azure AI Search     │        │    Azure OpenAI                       │   │
│  │                      │        │                                       │   │
│  │  chatops-ozguler     │        │  aoai-ep-swedencentral02              │   │
│  │  .search.windows.net │        │                                       │   │
│  │                      │        │  - gpt-5-nano (routing/synthesis)     │   │
│  │  - nport-funds-index │        │  - text-embedding-3-small             │   │
│  │  - imf_raptor        │        │                                       │   │
│  └──────────────────────┘        └──────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Network Architecture

```
VNet: vnet-fund-rag (10.0.0.0/16)
├── subnet-aks (10.0.0.0/22) - AKS nodes
├── subnet-appservice (10.0.4.0/24) - App Service VNet integration
└── subnet-privateendpoint (10.0.5.0/24) - PostgreSQL private endpoint

Private DNS Zone: privatelink.postgres.database.azure.com
└── A record: aistartupstr → 10.0.5.4
```

## Request Flow

```
1. User enters message in chat UI
2. Frontend checks PII via /api/pii → PII Container (eastus)
   ├── If PII detected → RED animation, message blocked
   └── If clean → GREEN animation, proceed
3. Frontend sends to /api/chat → AKS Backend
4. Backend routes query:
   ├── SQL route → PostgreSQL (via private endpoint)
   ├── SEMANTIC route → Azure AI Search (nport-funds-index)
   ├── RAPTOR route → Azure AI Search (imf_raptor)
   └── HYBRID route → Parallel SQL + Semantic + RAPTOR
5. Backend synthesizes answer using Azure OpenAI
6. Response streamed back to frontend via SSE
```

## Critical UI/UX Requirements

### PII Protection UI (MUST MAINTAIN)

The message composer (`src/components/chat/message-composer.tsx`) MUST include prominent PII detection feedback with the following states:

#### 1. Idle State
- Shows "PII Protected" badge with shield icon
- Neutral gray styling

#### 2. Scanning State (when user submits)
- **Amber/yellow color scheme**
- Animated scanning line that moves vertically across the input area
- Pulsing border animation
- Rotating scan icon in the status badge
- Button changes to amber with spinning scan icon
- User cannot submit while scanning

#### 3. Success State (PII check passed)
- **Green color scheme**
- Full overlay green flash effect
- Green checkmark badge appears in corner
- Success banner slides down with:
  - Green shield check icon in circle
  - "Security Check Passed" title
  - "No personal information detected" subtitle
  - Lock icon
- Input border turns green
- Button turns green with checkmark
- Status badge shows "Secure" with checkmarks
- Banner auto-hides after 2 seconds
- State returns to idle after 3 seconds

#### 4. Blocked State (PII detected)
- **Red color scheme**
- Full overlay red flash with glow effect
- Red X badge appears in corner with shake animation
- Error banner slides down with shake animation containing:
  - Red shield X icon in circle
  - "Message Blocked - PII Detected" title with warning icon
  - Detailed error message from API
  - Detected PII category pills (e.g., "US Social Security Number", "Credit Card Number")
- Input border turns red with red background tint
- Button turns red with X icon that shakes
- Status badge shows "Blocked" with pulsing shield
- Helper text changes to "Please remove personal information and try again"
- State persists until user modifies input

### Animation Library
Uses Framer Motion for all animations. Key animations:
- `AnimatePresence` for enter/exit transitions
- Spring animations for bouncy effects
- Shake animations for error states
- Rotation animations for scanning

### PII Categories Detected
The system blocks these banking-relevant PII types:
- USSocialSecurityNumber
- CreditCardNumber
- USBankAccountNumber
- InternationalBankingAccountNumber (IBAN)
- SWIFTCode

## Local Development

### Frontend (Next.js 15 + React 19)
- **Port: 3001** (configured in package.json)
- Run with: `npm run dev` from `src/` directory
- `/api/chat` - Proxies to Python backend
- `/api/pii` - PII detection endpoint (proxies to Azure PII container)

### PII Container (Azure Container Instances)
- **Endpoint:** `http://pii-ozguler.eastus.azurecontainer.io:5000`
- Service: Azure Language Service PII detection container
- Purpose: On-prem simulation - filters PII before messages reach AI
- No authentication required (container handles billing internally)

### Backend (Flask)
- Port: 5001
- `/api/chat` - RAG query endpoint
- Supports two retrieval modes: "code-rag" and "foundry-iq"
- Set `USE_POSTGRES=true` to use PostgreSQL instead of SQLite

### Data Sources
- PostgreSQL (production): 15 tables, 490K holdings from SEC N-PORT in `nport_funds` schema
- SQLite (local dev): Same data in `nport_funds.db`
- Azure AI Search: nport-funds-index (semantic search)
- RAPTOR Index: IMF economic outlook summaries

## Key Files
- `src/components/chat/message-composer.tsx` - Chat input with PII UI
- `src/app/api/chat/route.ts` - Chat API route
- `src/app/api/pii/route.ts` - PII detection route
- `src/lib/pii.ts` - PII detection logic
- `src/pii_filter.py` - Python PII filter
- `src/unified_retriever.py` - Multi-source RAG retriever
- `src/api_server.py` - Flask backend
- `k8s/` - Kubernetes manifests for AKS deployment
- `Dockerfile.backend` - Backend container image
- `Dockerfile.frontend` - Frontend container image
- `.github/workflows/` - CI/CD pipelines

## Deployment

### Azure Resources (rg-fund-rag)
| Resource | Name | Purpose |
|----------|------|---------|
| App Service | fundrag-frontend | Next.js frontend |
| App Service Plan | plan-fundrag-frontend | P1V3 Linux |
| AKS Cluster | aks-fund-rag | Backend (1-2 nodes autoscale) |
| VNet | vnet-fund-rag | Network isolation |
| Private Endpoint | pe-postgres-fundrag | PostgreSQL access |
| Private DNS Zone | privatelink.postgres.database.azure.com | DNS resolution |

### Container Registry
- ACR: `aistartuptr.azurecr.io`
- Image: `fund-rag-backend:latest`

### GitHub Actions Workflows
- `deploy-backend.yaml` - Build and deploy backend to AKS
- `deploy-frontend.yaml` - Build and deploy frontend to App Service
- `migrate-database.yaml` - Run PostgreSQL migration (manual trigger)

## Performance Optimizations Applied
- LLM routing disabled by default (uses fast heuristic routing)
- Streaming delay reduced to 5ms
- PII timeout reduced to 5s
- PostgreSQL with proper indexes for fast queries
- AKS autoscaling 1-2 nodes based on load

## Environment Variables

### Backend (AKS ConfigMap)
```
AZURE_OPENAI_ENDPOINT
AZURE_OPENAI_DEPLOYMENT_NAME
AZURE_TEXT_EMBEDDING_DEPLOYMENT_NAME
AZURE_SEARCH_ENDPOINT
PII_ENDPOINT
PGHOST, PGPORT, PGDATABASE, PGUSER
USE_POSTGRES=true
```

### Backend Secrets (AKS Secret)
```
AZURE_OPENAI_API_KEY
AZURE_SEARCH_ADMIN_KEY
PGPASSWORD
```

### Frontend (App Service)
```
AZURE_OPENAI_API_KEY
AZURE_OPENAI_ENDPOINT
PII_ENDPOINT
NEXTAUTH_SECRET
NEXTAUTH_URL
```
