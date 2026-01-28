<p align="center">
  <img src="https://img.shields.io/badge/Azure-Deployed-0078D4?style=for-the-badge&logo=microsoft-azure" alt="Azure Deployed">
  <img src="https://img.shields.io/badge/Next.js-15-black?style=for-the-badge&logo=next.js" alt="Next.js 15">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/PII-Protected-success?style=for-the-badge&logo=shield" alt="PII Protected">
</p>

<h1 align="center">Fund Intelligence</h1>

<p align="center">
  <strong>AI-powered mutual fund analysis with enterprise-grade security</strong>
</p>

<p align="center">
  Ask questions about 490,000+ fund holdings in plain English.<br>
  Get verified answers with full source citations.<br>
  Protected by multi-layer PII detection.
</p>

<p align="center">
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-features">Features</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-query-types">Query Types</a> •
  <a href="#-deployment">Deployment</a>
</p>

---

## The Problem

Financial analysts spend **hours** querying multiple systems to analyze mutual fund data, cross-reference holdings, and incorporate macroeconomic context into investment decisions.

## Our Solution

A natural language interface that combines **SEC N-PORT filings** with **IMF World Economic Outlook** to deliver instant, cited answers with enterprise security.

```
You: "Best bond funds given IMF's rate outlook"

Fund Intelligence: Based on IMF's projection for rate cuts in H2 2025,
I recommend duration-sensitive funds:

1. Vanguard Long-Term Treasury ($89.2B) - Maximum rate sensitivity [1]
2. PIMCO Income Fund ($142.7B) - Quality yield with MBS exposure [2]
3. MetWest Total Return ($78.4B) - Diversified duration play [3]

Sources: [1] SEC N-PORT Q4 2024, [2] SEC N-PORT Q4 2024, [3] IMF WEO Oct 2024
```

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 🧠 Intelligent Query Routing
Automatically selects the optimal retrieval strategy—SQL, semantic search, or economic context—based on your question.

### 🔒 Enterprise PII Protection
Multi-layer security blocks sensitive data (SSN, credit cards, bank accounts) with real-time visual feedback.

### 📊 Comprehensive Data
490K+ holdings from SEC N-PORT filings combined with IMF economic projections.

</td>
<td width="50%">

### ⚡ Real-time Streaming
Server-sent events deliver responses word-by-word for a natural chat experience.

### 📝 Full Citations
Every answer includes source provenance with confidence scores—no black boxes.

### 🔄 Dual Retrieval Modes
Choose between full-control Code-based RAG or Azure-managed Foundry IQ.

</td>
</tr>
</table>

---

## 📊 Data at a Glance

<table>
<tr>
<td align="center"><h3>250</h3>Mutual Funds</td>
<td align="center"><h3>490K+</h3>Holdings</td>
<td align="center"><h3>572K</h3>Security IDs</td>
<td align="center"><h3>305K</h3>Debt Securities</td>
</tr>
</table>

**Sources:**
- **SEC N-PORT** — Quarterly regulatory filings with fund assets, holdings, risk metrics, derivatives
- **IMF WEO** — World Economic Outlook with inflation forecasts, growth projections, rate expectations

---

## 🎯 Query Types

| Type | Use Case | Example |
|:-----|:---------|:--------|
| **SQL** | Precise data lookups | *"Top 10 funds by AUM"* |
| **Semantic** | Style & similarity | *"Conservative income funds"* |
| **RAPTOR** | Economic outlook | *"IMF inflation forecast 2025"* |
| **Hybrid** | Fund + macro combined | *"Best bonds for rate cuts"* |
| **Chain** | Multi-step reasoning | *"Position portfolio for IMF outlook"* |

<details>
<summary><strong>See more example queries →</strong></summary>

### SQL Queries
- "Which funds hold NVIDIA stock?"
- "Show funds with DV01 exposure > $5M"
- "List all Vanguard funds over $50B AUM"

### Semantic Queries
- "Funds similar to PIMCO Income Fund"
- "Growth-oriented equity funds"
- "Low-risk bond funds for retirement"

### Hybrid Queries
- "Top funds considering inflation outlook"
- "Duration-sensitive funds for rate cut scenario"

### Chain Queries
- "Best funds if inflation rises above 3%"
- "Which funds benefit from EM recovery?"

### RAPTOR Queries
- "Global recession risk according to IMF"
- "Summarize IMF views on emerging markets"

</details>

---

## 🏗 Architecture

### Cloud Infrastructure

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              AZURE                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌─────────────┐      ┌─────────────┐      ┌─────────────────────┐    │
│   │ App Service │      │     AKS     │      │    PostgreSQL       │    │
│   │  (Next.js)  │─────▶│   (Flask)   │─────▶│   (Private EP)      │    │
│   │             │      │             │      │                     │    │
│   │  Frontend   │      │  RAG Logic  │      │  250 funds          │    │
│   │  PII UI     │      │  5 Routes   │      │  490K holdings      │    │
│   └──────┬──────┘      └──────┬──────┘      └─────────────────────┘    │
│          │                    │                                         │
│          ▼                    ▼                                         │
│   ┌─────────────┐      ┌─────────────┐      ┌─────────────────────┐    │
│   │     PII     │      │  AI Search  │      │    Azure OpenAI     │    │
│   │  Container  │      │             │      │                     │    │
│   │             │      │  • funds    │      │  • gpt-5-nano       │    │
│   │  Language   │      │  • imf      │      │  • embeddings       │    │
│   │  Service    │      │    raptor   │      │                     │    │
│   └─────────────┘      └─────────────┘      └─────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Request Flow

```
User Query → PII Check → Route → Retrieve → Synthesize → Stream Response
     │           │          │         │           │            │
     │      Block if      Auto-    Parallel    Combine      5ms/word
     │      detected     classify   fetch      sources      streaming
```

### Network Security

- **VNet Isolation** — All services in private subnet
- **Private Endpoints** — Database accessible only via internal IP
- **PII Container** — On-premises simulation for compliance

---

## 🔄 Two Retrieval Paths

<table>
<tr>
<th width="50%">Code-Based RAG</th>
<th width="50%">Foundry IQ</th>
</tr>
<tr>
<td>

**5 Routes** — Full routing control

✅ SQL, Semantic, RAPTOR, Hybrid, Chain
✅ IMF macro context
✅ Multi-step reasoning
✅ Detailed citations

Best for: **Development, complex queries**

</td>
<td>

**3 Routes** — Azure-managed

✅ SQL, Semantic, Hybrid
✅ Azure AD authentication
✅ Built-in tracing
✅ Managed updates

Best for: **Production, simplicity**

</td>
</tr>
</table>

---

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- Python 3.10+
- Azure subscription (OpenAI, AI Search, Language Service)

### 1. Clone & Install

```bash
git clone https://github.com/ozgurgulerx/pii-fund-rag.git
cd pii-fund-rag/fund-rag-poc/src

# Frontend
npm install

# Backend
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.local.example .env.local
```

```env
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-instance.openai.azure.com
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-5-nano

# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_ADMIN_KEY=your-key

# PII Container
PII_ENDPOINT=http://your-pii-container:5000
```

### 3. Run

```bash
# Terminal 1: Backend
python api_server.py  # → localhost:5001

# Terminal 2: Frontend
npm run dev  # → localhost:3001
```

### 4. Open

```
http://localhost:3001/chat
```

---

## 🔒 PII Protection

Real-time detection with visual feedback:

| State | Experience |
|:------|:-----------|
| **Idle** | Gray shield badge |
| **Scanning** | Amber pulse animation |
| **Passed** ✓ | Green flash → proceed |
| **Blocked** ✗ | Red shake → shows detected categories |

**Protected categories:** SSN, Credit Card, Bank Account, IBAN, SWIFT, Driver's License, Passport, Tax ID, Email, Phone, Address

---

## 📁 Project Structure

```
fund-rag-poc/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── api/chat/           # Chat endpoint
│   │   └── chat/               # Chat UI
│   ├── components/             # React components
│   ├── api_server.py           # Flask backend
│   ├── unified_retriever.py    # RAG orchestrator
│   ├── query_router.py         # Route classification
│   └── foundry_agent_client.py # Foundry IQ
├── k8s/                        # Kubernetes manifests
├── .github/workflows/          # CI/CD
└── README.md
```

---

## ☁️ Deployment

### Azure Resources

| Resource | Service | Purpose |
|:---------|:--------|:--------|
| `fundrag-frontend` | App Service | Next.js UI |
| `aks-fund-rag` | AKS | Flask backend |
| `aistartupstr` | PostgreSQL | Fund data |
| `chatops-ozguler` | AI Search | Semantic indexes |
| `pii-ozguler` | Container Instance | PII detection |

### CI/CD

| Workflow | Trigger | Action |
|:---------|:--------|:-------|
| `deploy-backend.yaml` | Push to main | Build → ACR → AKS |
| `deploy-frontend.yaml` | Push to main | Build → App Service |

---

## ⚡ Performance

| Metric | Value |
|:-------|:------|
| Query routing | ~0ms (heuristic) |
| SQL execution | <500ms |
| Vector search | <200ms |
| Response streaming | 5ms/word |

---

## 📄 License

Proprietary — Internal use only.

---

<p align="center">
  <strong>Built with ❤️ for financial intelligence</strong>
</p>
