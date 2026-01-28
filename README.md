# Fund Intelligence RAG System

An enterprise-grade Retrieval-Augmented Generation (RAG) chatbot for querying mutual fund data using natural language. Combines SEC N-PORT filings with IMF World Economic Outlook for comprehensive fund analysis with multi-layer PII protection.

## Features

- **Natural Language Queries** - Ask questions about mutual funds in plain English
- **5 Intelligent Query Routes** - Automatic routing to optimal retrieval strategy
- **Multi-Source RAG** - Combines SQL, semantic search, and economic context
- **PII Protection** - Multi-layer security with visual feedback
- **Dual Retrieval Modes** - Code-based RAG or Azure AI Foundry managed agent
- **Real-time Streaming** - Server-sent events for fast response display
- **Full Citations** - Source provenance with confidence scores

## Data Sources

### SEC N-PORT Filings (Q4 2024)

| Metric | Value |
|--------|-------|
| Funds | 250 |
| Holdings | 490,447 |
| Security Identifiers | 572,768 |
| Debt Securities | 305,413 |

**Available Data:**
- Fund assets, liabilities, monthly flows
- Individual holdings with CUSIP, position size, asset category
- Interest rate risk (DV01 by tenor)
- Credit spreads (investment grade vs non-investment grade)
- Derivatives, securities lending, counterparty information

### IMF World Economic Outlook (RAPTOR Index)

Hierarchical index of IMF economic projections:
- Inflation forecasts
- GDP growth projections
- Interest rate expectations
- Emerging market analysis

## Query Types

| Route | Description | Example |
|-------|-------------|---------|
| **SQL** | Precise data lookups | "Top 10 funds by AUM" |
| **Semantic** | Style/similarity search | "Conservative income funds" |
| **RAPTOR** | Economic outlook queries | "IMF inflation outlook 2025" |
| **Hybrid** | Fund + macro combined | "Best bonds for rate cuts" |
| **Chain** | Macro-driven selection | "Position portfolio for IMF forecast" |

## Architecture

### Cloud Deployment (Azure)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AZURE DEPLOYMENT                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────┐        ┌──────────────────────────────────────┐   │
│  │   Azure App Service  │        │     Azure Kubernetes Service (AKS)   │   │
│  │   (Frontend)         │        │     (Backend)                        │   │
│  │                      │        │                                      │   │
│  │  Next.js 15 + React  │───────▶│  Flask API + RAG Logic               │   │
│  │  PII UI animations   │  API   │  /api/chat, /health                  │   │
│  └──────────┬───────────┘        └──────────────┬───────────────────────┘   │
│             │                                    │                          │
│             │ PII Check                          │ Data Access              │
│             ▼                                    ▼                          │
│  ┌──────────────────────┐        ┌──────────────────────────────────────┐   │
│  │  Azure Container     │        │    Azure PostgreSQL (Private EP)     │   │
│  │  Instances (PII)     │        │    250 funds, 490K holdings          │   │
│  │  Language AI Service │        │    nport_funds schema                │   │
│  └──────────────────────┘        └──────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────┐        ┌──────────────────────────────────────┐   │
│  │  Azure AI Search     │        │    Azure OpenAI                      │   │
│  │  • nport-funds-index │        │    • gpt-5-nano (routing/synthesis)  │   │
│  │  • imf_raptor        │        │    • text-embedding-3-small          │   │
│  └──────────────────────┘        └──────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Network Architecture

```
VNet: vnet-fund-rag (10.0.0.0/16)
├── subnet-aks (10.0.0.0/22) - AKS nodes
├── subnet-appservice (10.0.4.0/24) - App Service VNet integration
└── subnet-privateendpoint (10.0.5.0/24) - PostgreSQL private endpoint

Private DNS Zone: privatelink.postgres.database.azure.com
```

### Request Flow

```
User Query → PII Check → Route Classification → Retrieval → Synthesis → Response

1. User enters message in chat UI
2. Frontend checks PII via Azure Language Service container
   ├── If PII detected → RED animation, message blocked
   └── If clean → GREEN animation, proceed
3. Backend classifies query into one of 5 routes
4. Execute retrieval:
   ├── SQL → PostgreSQL
   ├── SEMANTIC → Azure AI Search (nport-funds-index)
   ├── RAPTOR → Azure AI Search (imf_raptor)
   └── HYBRID → All three in parallel
5. LLM synthesizes answer with citations
6. Stream response back to frontend (SSE)
```

## Two Retrieval Modes

### Code-Based RAG (Default)

Full control with 5 query routes including macro context:

```python
retriever = UnifiedRetriever()
result = retriever.answer("Best bond funds given IMF outlook")
# Routes: SQL, SEMANTIC, RAPTOR, HYBRID, CHAIN
```

### Foundry IQ (Azure Managed)

Azure AI Foundry managed agent with 3 routes:

```python
client = FoundryAgentClient()
result = client.chat("Top 10 bond funds")
# Routes: SQL, SEMANTIC, HYBRID
```

| Aspect | Code-Based RAG | Foundry IQ |
|--------|----------------|------------|
| Routes | 5 | 3 |
| IMF Macro Context | Yes | No |
| Multi-step Reasoning | Yes (Chain) | No |
| Best For | Complex queries | Production simplicity |

## Project Structure

```
fund-rag-poc/
├── src/                          # Frontend (Next.js) + Backend (Python)
│   ├── app/                      # Next.js App Router
│   │   ├── api/
│   │   │   ├── chat/route.ts     # Chat API (proxies to Flask)
│   │   │   └── pii/route.ts      # PII detection endpoint
│   │   └── chat/page.tsx         # Main chat UI
│   ├── components/
│   │   ├── chat/
│   │   │   ├── chat-thread.tsx   # Message display + query suggestions
│   │   │   ├── message-composer.tsx  # PII-protected input
│   │   │   └── follow-up-chips.tsx   # Suggestion chips
│   │   └── layout/
│   │       ├── sidebar.tsx       # Conversation list
│   │       └── sources-panel.tsx # Citations viewer
│   ├── data/seed.ts              # Query categories + sample data
│   ├── lib/pii.ts                # PII detection logic
│   │
│   ├── api_server.py             # Flask backend
│   ├── unified_retriever.py      # Multi-source RAG orchestrator
│   ├── query_router.py           # Route classification
│   ├── sql_generator.py          # LLM-based SQL generation
│   ├── fund_rag_agent.py         # Standalone RAG agent
│   ├── foundry_agent_client.py   # Foundry IQ wrapper
│   └── pii_filter.py             # Python PII filter
│
├── k8s/                          # Kubernetes manifests for AKS
├── .github/workflows/            # CI/CD pipelines
├── Dockerfile.backend            # Backend container
├── Dockerfile.frontend           # Frontend container
└── nport_funds.db                # SQLite database (local dev)
```

## Local Development

### Prerequisites

- Node.js 18+
- Python 3.10+
- Azure subscription with:
  - Azure OpenAI (gpt-5-nano, text-embedding-3-small)
  - Azure AI Search
  - Azure Language Service (PII container)

### Setup

1. **Clone and install dependencies:**
```bash
cd fund-rag-poc/src
npm install
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
cp .env.local.example .env.local
# Edit .env.local with your Azure credentials
```

3. **Start backend:**
```bash
python api_server.py
# Runs on http://localhost:5001
```

4. **Start frontend:**
```bash
npm run dev
# Runs on http://localhost:3001
```

5. **Open the app:**
```
http://localhost:3001/chat
```

### Environment Variables

```bash
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-5-nano
AZURE_TEXT_EMBEDDING_DEPLOYMENT_NAME=text-embedding-3-small

# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_ADMIN_KEY=your-key

# PII Container
PII_ENDPOINT=http://your-pii-container:5000

# PostgreSQL (production)
PGHOST=your-postgres.postgres.database.azure.com
PGPORT=5432
PGDATABASE=fundrag
PGUSER=your-user
PGPASSWORD=your-password
USE_POSTGRES=true
```

## Azure Deployment

### Resources (rg-fund-rag)

| Resource | Name | Purpose |
|----------|------|---------|
| App Service | fundrag-frontend | Next.js frontend |
| AKS Cluster | aks-fund-rag | Backend (1-2 nodes autoscale) |
| PostgreSQL | aistartupstr | Fund data (private endpoint) |
| AI Search | chatops-ozguler | Semantic indexes |
| Container Instance | pii-ozguler | PII detection |

### CI/CD Pipelines

| Workflow | Trigger | Action |
|----------|---------|--------|
| deploy-backend.yaml | Push to main | Build → ACR → AKS |
| deploy-frontend.yaml | Push to main | Build → App Service |
| migrate-database.yaml | Manual | PostgreSQL migrations |

### Deploy Commands

```bash
# Backend to AKS
kubectl apply -f k8s/

# Frontend to App Service
az webapp deployment source config-zip \
  --resource-group rg-fund-rag \
  --name fundrag-frontend \
  --src dist.zip
```

## PII Protection

### Protected Categories

- US Social Security Number
- Credit Card Number
- US Bank Account Number
- IBAN, SWIFT Code
- Driver's License, Passport
- Email, Phone, Address

### User Experience States

| State | Visual Feedback |
|-------|-----------------|
| Idle | Gray "PII Protected" badge |
| Scanning | Amber animation, pulsing border |
| Passed | Green flash, "Security Check Passed" |
| Blocked | Red flash + shake, shows detected categories |

## Sample Queries

### SQL Queries
- "Top 10 funds by total net assets"
- "Which funds hold NVIDIA stock?"
- "Show funds with DV01 exposure > $5M"

### Semantic Queries
- "Conservative income-focused funds"
- "Funds similar to PIMCO Income Fund"
- "Growth-oriented equity funds"

### Hybrid Queries
- "Best bond funds given current rate environment"
- "Top funds considering inflation outlook"

### Chain Queries
- "How should I position my portfolio for IMF's growth forecast?"
- "Best funds if inflation rises above 3%"

### RAPTOR Queries
- "What's the IMF's inflation outlook for 2025?"
- "Global recession risk according to IMF"

## Performance

| Metric | Value |
|--------|-------|
| Heuristic routing | ~0ms |
| SQL query latency | <500ms |
| Vector search | <200ms |
| Streaming delay | 5ms/word |
| PII check timeout | 5s |

## License

Proprietary - Internal use only.

## Support

For issues or questions, contact the development team or open an issue in this repository.
