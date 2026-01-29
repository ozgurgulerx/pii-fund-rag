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
BACKEND_URL              # CRITICAL: Must point to internal LoadBalancer IP
WEBSITE_VNET_ROUTE_ALL=1 # Required for VNet routing to AKS
PORT=3000                # Next.js server port
WEBSITES_PORT=3000       # Azure port mapping
```

## Troubleshooting Guide

### Quick Health Check Commands

```bash
# 1. Check AKS backend health
kubectl get pods -n fund-rag
kubectl logs -n fund-rag -l app=fund-rag-backend --tail=50
curl http://<INTERNAL-LB-IP>/health

# 2. Check App Service frontend
az webapp log tail --name fundrag-frontend --resource-group rg-fund-rag
curl https://fundrag-frontend.azurewebsites.net/api/pii -X POST -H "Content-Type: application/json" -d '{"text":"test"}'

# 3. Check PII container
curl -X POST "http://pii-ozguler.eastus.azurecontainer.io:5000/language/:analyze-text?api-version=2023-04-01" \
  -H "Content-Type: application/json" \
  -d '{"kind":"PiiEntityRecognition","parameters":{"modelVersion":"latest"},"analysisInput":{"documents":[{"id":"1","language":"en","text":"SSN 123-45-6789"}]}}'

# 4. Get internal LoadBalancer IP
kubectl get svc fund-rag-backend-internal -n fund-rag -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```

### Common Issues and Fixes

#### Issue: Empty chat responses
**Symptoms:** User sends message, gets empty or no response
**Root Causes:**
1. `BACKEND_URL` not set or pointing to wrong IP
2. VNet routing not enabled
3. Backend pods not running

**Fix:**
```bash
# Verify BACKEND_URL points to internal LoadBalancer
az webapp config appsettings list --name fundrag-frontend --resource-group rg-fund-rag --query "[?name=='BACKEND_URL']"

# Must be: http://10.0.0.10 (internal LB IP)
# NOT: http://10.0.8.60:5001 (ClusterIP - unreachable from App Service)

az webapp config appsettings set --name fundrag-frontend --resource-group rg-fund-rag \
  --settings BACKEND_URL="http://10.0.0.10" WEBSITE_VNET_ROUTE_ALL=1
```

#### Issue: PII UI animations not showing
**Symptoms:** PII check happens but no visual feedback
**Root Causes:**
1. Framer Motion not loading
2. CSS not bundled correctly
3. Frontend not deployed with latest code

**Verify PII API works:**
```bash
curl -X POST "https://fundrag-frontend.azurewebsites.net/api/pii" \
  -H "Content-Type: application/json" \
  -d '{"text":"My SSN is 123-45-6789"}'
# Should return: {"blocked":true,"message":"...","detectedCategories":["USSocialSecurityNumber"]}
```

#### Issue: PII check timing out
**Symptoms:** Long delay before message sends, PII check fails
**Root Causes:**
1. VNet Route All blocking external traffic
2. PII container not reachable

**Fix:** PII container (4.157.124.30) is external to VNet. With WEBSITE_VNET_ROUTE_ALL=1, ensure VNet has internet gateway access.

### Integration Points to Test

| Component | Endpoint | Expected Response |
|-----------|----------|-------------------|
| Frontend health | `GET /` | HTML page |
| PII API (clean) | `POST /api/pii {"text":"hello"}` | `{"blocked":false}` |
| PII API (blocked) | `POST /api/pii {"text":"SSN 123-45-6789"}` | `{"blocked":true,"detectedCategories":["USSocialSecurityNumber"]}` |
| Chat API | `POST /api/chat {"messages":[...]}` | SSE stream with `data: {"type":"text",...}` |
| Backend health | `GET /health` (internal) | `{"status":"ok"}` |
| PII Container | `POST /language/:analyze-text` | PII detection results |

### Network Configuration Reference

```
App Service (fundrag-frontend)
├── VNet Integration: subnet-appservice (10.0.4.0/24)
├── WEBSITE_VNET_ROUTE_ALL: 1 (route ALL traffic through VNet)
└── Outbound to:
    ├── AKS Internal LB: 10.0.0.10:80 (via VNet)
    ├── PII Container: pii-ozguler.eastus.azurecontainer.io:5000 (via VNet → Internet)
    └── Azure OpenAI: aoai-ep-swedencentral02 (via VNet → Internet)

AKS Cluster (aks-fund-rag)
├── VNet: subnet-aks (10.0.0.0/22)
├── Services:
│   ├── fund-rag-backend (ClusterIP): 10.0.8.60:5001 (internal only)
│   ├── fund-rag-backend-lb (LoadBalancer): 20.71.11.129:80 (public)
│   └── fund-rag-backend-internal (LoadBalancer): 10.0.0.10:80 (VNet-internal) ← USE THIS
└── Outbound to:
    ├── PostgreSQL: 10.0.5.4 (via private endpoint)
    ├── Azure AI Search: chatops-ozguler.search.windows.net
    └── Azure OpenAI: aoai-ep-swedencentral02
```

### PII UI/UX Component Integration

The PII detection flow connects API responses to UI states in `message-composer.tsx`:

```
API Response                          UI State & Animation
─────────────────────────────────────────────────────────────────
fetch("/api/pii")                 →  piiStatus = "checking"
                                     - Amber scanning overlay
                                     - Animated scan line
                                     - Pulsing border
                                     - Rotating scan icon

{"blocked": false}                →  piiStatus = "passed"
                                     - Green flash overlay
                                     - Corner checkmark badge
                                     - Success banner (2s)
                                     - Green input border
                                     → Returns to "idle" after 3s

{"blocked": true,                 →  piiStatus = "blocked"
 "detectedCategories": [...]}        - Red flash + glow overlay
                                     - Shake animation on banner
                                     - Category pills display
                                     - Red input border persists
                                     - "Restore message" button
                                     → Stays blocked until user edits

Network error                     →  piiStatus = "idle" (fail open)
                                     - Toast: "Security check unavailable"
                                     - Message proceeds without PII check
```

### Deployment Checklist

Before deploying, verify:

- [ ] `BACKEND_URL` set to internal LoadBalancer IP (`http://10.0.0.10`)
- [ ] `WEBSITE_VNET_ROUTE_ALL=1` enabled
- [ ] `PII_ENDPOINT` set to PII container (`http://pii-ozguler.eastus.azurecontainer.io:5000`)
  - ⚠️ **ALWAYS use DNS name, NOT IP address!** ACI IPs can change on restart/redeploy
- [ ] `PORT=3000` and `WEBSITES_PORT=3000` configured
- [ ] AKS pods running: `kubectl get pods -n fund-rag`
- [ ] Internal LoadBalancer has IP: `kubectl get svc fund-rag-backend-internal -n fund-rag`
- [ ] Backend health check passes
- [ ] PII container responds to health check

### Frontend Deployment (Next.js Standalone)

The frontend uses Next.js standalone output. Deployment structure:
```
wwwroot/
├── server.js           # Next.js server entry point
├── package.json        # Dependencies
├── node_modules/       # Production dependencies only
├── .next/
│   └── static/         # Static assets (CSS, JS, fonts)
└── public/             # Public assets
```

**Startup command:** `node server.js`

### Backend Kubernetes Services

Three services exist for different access patterns:
```yaml
# ClusterIP (internal K8s only) - DON'T use from App Service
fund-rag-backend: 10.0.8.60:5001

# Public LoadBalancer - for external testing
fund-rag-backend-lb: 20.71.11.129:80

# Internal LoadBalancer - USE THIS for App Service
fund-rag-backend-internal: 10.0.0.10:80
```

---

## CRITICAL: Deployment & Recovery Procedures

### DO NOT CHANGE These Settings (Will Break Deployment)

| Setting | Required Value | Reason |
|---------|---------------|--------|
| `BACKEND_URL` | `http://10.0.0.10` | Internal LoadBalancer IP, not ClusterIP |
| `WEBSITE_VNET_ROUTE_ALL` | `1` | Routes traffic through VNet to reach AKS |
| `PORT` | `3000` | Next.js server listens on this port |
| `WEBSITES_PORT` | `3000` | Azure routes traffic to this port |
| Startup command | `node server.js` | Entry point for Next.js standalone |

### Correct Frontend Deployment Procedure

**IMPORTANT:** Do not deploy via `az webapp deployment source config-zip` with incorrect structure.

The Next.js standalone output has a nested path structure. Correct deployment:

```bash
# 1. Build the frontend
cd /path/to/fund-rag-poc/src
npm run build

# 2. Create deployment package
rm -rf /tmp/frontend-final && mkdir -p /tmp/frontend-final/.next

# 3. Copy standalone app (note: path structure is embedded)
cp .next/standalone/Developer/Projects/af-pii-funds/fund-rag-poc/src/server.js /tmp/frontend-final/
cp .next/standalone/Developer/Projects/af-pii-funds/fund-rag-poc/src/package.json /tmp/frontend-final/
cp -r .next/standalone/Developer/Projects/af-pii-funds/fund-rag-poc/src/node_modules /tmp/frontend-final/
cp -r .next/standalone/Developer/Projects/af-pii-funds/fund-rag-poc/src/.next/* /tmp/frontend-final/.next/

# 4. Add static files (CRITICAL - must be separate step)
cp -r .next/static /tmp/frontend-final/.next/static
mkdir -p /tmp/frontend-final/public

# 5. Verify structure before deploy
ls /tmp/frontend-final/
# Should show: node_modules  package.json  public  server.js  .next

ls /tmp/frontend-final/.next/
# Should show: server  static  BUILD_ID  *.json manifests

# 6. Deploy
cd /tmp/frontend-final
zip -r /tmp/app.zip . -x "*.DS_Store"
az webapp deploy --resource-group rg-fund-rag --name fundrag-frontend \
  --src-path /tmp/app.zip --type zip --restart true
```

### Emergency Recovery: Frontend Down

If the frontend shows "Application Error":

```bash
# 1. Quick health check
curl -s "https://fundrag-frontend.azurewebsites.net/api/pii" \
  -X POST -H "Content-Type: application/json" -d '{"text":"test"}'
# If this fails, frontend needs redeployment

# 2. Verify App Service settings
az webapp config appsettings list --name fundrag-frontend \
  --resource-group rg-fund-rag -o table | grep -E "BACKEND_URL|PORT|VNET"

# Expected output:
# BACKEND_URL  http://10.0.0.10
# PORT         3000
# WEBSITES_PORT 3000
# WEBSITE_VNET_ROUTE_ALL 1

# 3. If settings wrong, fix them:
az webapp config appsettings set --name fundrag-frontend \
  --resource-group rg-fund-rag --settings \
  BACKEND_URL="http://10.0.0.10" \
  WEBSITE_VNET_ROUTE_ALL=1 \
  PORT=3000 \
  WEBSITES_PORT=3000

# 4. Restart
az webapp restart --name fundrag-frontend --resource-group rg-fund-rag

# 5. If still broken, redeploy using procedure above
```

### Emergency Recovery: Backend/Chat Not Working

```bash
# 1. Check backend pods
kubectl get pods -n fund-rag
# All pods should show Running status

# 2. Check backend logs
kubectl logs -n fund-rag -l app=fund-rag-backend --tail=50

# 3. Verify internal LoadBalancer
kubectl get svc fund-rag-backend-internal -n fund-rag
# Should show EXTERNAL-IP: 10.0.0.10

# 4. Test backend health from within cluster
kubectl run curl-test --image=curlimages/curl --rm -it --restart=Never \
  -n fund-rag -- curl -s http://fund-rag-backend:5001/health

# 5. If pods crashing, check for OOM or config issues
kubectl describe pod -n fund-rag -l app=fund-rag-backend | grep -A5 "Last State"
```

### Testing After Any Change

Always test these endpoints after deployment:

```bash
# 1. PII Clean (should return blocked:false)
curl -s "https://fundrag-frontend.azurewebsites.net/api/pii" \
  -X POST -H "Content-Type: application/json" -d '{"text":"hello"}'

# 2. PII Blocked (should return blocked:true with categories)
curl -s "https://fundrag-frontend.azurewebsites.net/api/pii" \
  -X POST -H "Content-Type: application/json" \
  -d '{"text":"SSN 123-45-6789"}'

# 3. Chat API (should return SSE stream)
curl -s "https://fundrag-frontend.azurewebsites.net/api/chat" \
  -X POST -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Top 3 funds"}]}' -m 60
```

### Code Changes That Break Things

**Frontend API routes (`src/app/api/`):**
- Changing `BACKEND_URL` or `PYTHON_API_URL` env var names
- Modifying SSE response format
- Breaking error handling in catch blocks

**Components (`src/components/chat/`):**
- Removing Framer Motion animations breaks PII UI
- Changing `piiStatus` state machine
- Modifying API call to `/api/pii`

**Backend (`src/api_server.py`):**
- Changing response JSON structure (`answer`, `route`, `citations`)
- Modifying port from 5001
- Breaking health endpoint

**Kubernetes (`k8s/`):**
- Removing `fund-rag-backend-internal` service
- Changing ports or selectors
- Modifying namespace from `fund-rag`

---

## GitHub Actions CI/CD Configuration (WORKING - DO NOT CHANGE)

### Azure OIDC Authentication Setup

The deployment uses **federated credentials** (OIDC) - no expiring secrets.

**App Registration:**
- App ID: `6b0857f6-4bcd-4014-8222-01e605a4d6c9`
- Display Name: `github-fundrag-deploy`
- Tenant: `16b3c013-d300-468d-ac64-7eda0820b6d3`

**Federated Credential:**
- Issuer: `https://token.actions.githubusercontent.com`
- Subject: `repo:ozgurgulerx/pii-fund-rag:ref:refs/heads/main`
- Audience: `api://AzureADTokenExchange`

**Service Principal:**
- Has **Contributor** role on `rg-fund-rag` resource group

### GitHub Secrets (Already Configured)

| Secret | Value |
|--------|-------|
| `AZURE_CLIENT_ID` | `6b0857f6-4bcd-4014-8222-01e605a4d6c9` |
| `AZURE_TENANT_ID` | `16b3c013-d300-468d-ac64-7eda0820b6d3` |
| `AZURE_SUBSCRIPTION_ID` | `a20bc194-9787-44ee-9c7f-7c3130e651b6` |

### If GitHub Actions Fails

1. **"Service principal missing"** error:
   ```bash
   az ad sp create --id 6b0857f6-4bcd-4014-8222-01e605a4d6c9
   az role assignment create --assignee 6b0857f6-4bcd-4014-8222-01e605a4d6c9 \
     --role Contributor \
     --scope /subscriptions/a20bc194-9787-44ee-9c7f-7c3130e651b6/resourceGroups/rg-fund-rag
   ```

2. **"Federated credential not found"** error:
   ```bash
   az ad app federated-credential create --id 498a7cd9-8785-4e09-a42c-4a1b7cdbdca1 --parameters '{
     "name": "github-main-branch",
     "issuer": "https://token.actions.githubusercontent.com",
     "subject": "repo:ozgurgulerx/pii-fund-rag:ref:refs/heads/main",
     "audiences": ["api://AzureADTokenExchange"]
   }'
   ```

### Workflow Triggers

The frontend deploys automatically when these paths change:
- `src/app/**`
- `src/components/**`
- `src/lib/**`
- `src/hooks/**`
- `src/types/**`
- `src/data/**`
- `src/package.json`
- `src/next.config.mjs`
- `src/tailwind.config.ts`

Or manually via `workflow_dispatch`.

---

## Current Working State (Checkpoint: 2026-01-29)

### Git Checkpoint
```bash
# Tag for known working state
git tag: checkpoint-2026-01-29
git commit: 33e9314

# To restore if anything breaks:
git checkout checkpoint-2026-01-29
```

### Verified Working Endpoints

| Endpoint | Test Command | Expected Result |
|----------|--------------|-----------------|
| Frontend | `curl https://fundrag-frontend.azurewebsites.net` | HTML page |
| PII (clean) | `curl -X POST https://fundrag-frontend.azurewebsites.net/api/pii -H "Content-Type: application/json" -d '{"text":"hello"}'` | `{"blocked":false}` |
| PII (blocked) | `curl -X POST https://fundrag-frontend.azurewebsites.net/api/pii -H "Content-Type: application/json" -d '{"text":"SSN 123-45-6789"}'` | `{"blocked":true,"detectedCategories":["USSocialSecurityNumber"]}` |
| Chat | `curl -X POST https://fundrag-frontend.azurewebsites.net/api/chat -H "Content-Type: application/json" -d '{"messages":[{"role":"user","content":"Top 3 funds"}]}'` | SSE stream with fund data |

### Infrastructure Health Check Workflow

A GitHub Actions workflow runs every 30 minutes to monitor and auto-recover infrastructure:
- **File:** `.github/workflows/infra-health-check.yaml`
- **Schedule:** `*/30 * * * *` (every 30 minutes)
- **Actions:** Checks AKS and PostgreSQL, auto-starts if stopped

**Known Issue:** The health check shows a permission error for PostgreSQL because the service principal only has access to `rg-fund-rag`, not `aistartupstr` (where PostgreSQL lives). This doesn't affect the actual system - PostgreSQL works fine via database credentials.

---

## WHEN SYSTEM IS DOWN - Quick Diagnosis

### Step 1: Identify What's Broken

```bash
# Test each component
curl -s https://fundrag-frontend.azurewebsites.net/api/pii -X POST \
  -H "Content-Type: application/json" -d '{"text":"test"}'

# If this fails → Frontend or PII container issue
# If returns {"blocked":false} → Frontend + PII working, check backend
```

### Step 2: Check Infrastructure Status

```bash
# Check if AKS is running
az aks show --resource-group rg-fund-rag --name aks-fund-rag --query powerState.code -o tsv
# Should return: Running

# Check if PostgreSQL is running
az postgres flexible-server show --name aistartupstr --resource-group aistartupstr --query state -o tsv
# Should return: Ready

# Check AKS pods
az aks get-credentials --resource-group rg-fund-rag --name aks-fund-rag --overwrite-existing
kubectl get pods -n fund-rag
# Should show 2 pods in Running state
```

### Step 3: Start Stopped Services

```bash
# Start PostgreSQL (if stopped)
az postgres flexible-server start --name aistartupstr --resource-group aistartupstr

# Start AKS (if stopped)
az aks start --resource-group rg-fund-rag --name aks-fund-rag

# Wait 2-3 minutes for AKS to fully start, then refresh credentials
az aks get-credentials --resource-group rg-fund-rag --name aks-fund-rag --overwrite-existing
kubectl get pods -n fund-rag
```

### Step 4: Verify Services After Recovery

```bash
# Check internal LoadBalancer IP
kubectl get svc fund-rag-backend-internal -n fund-rag
# Should show EXTERNAL-IP: 10.0.0.10

# Test backend health
kubectl exec -n fund-rag deployment/fund-rag-backend -- curl -s localhost:5001/health
# Should return: {"service":"fund-rag-api","status":"ok"}

# Test full flow
curl -s https://fundrag-frontend.azurewebsites.net/api/chat \
  -X POST -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Top 3 funds"}]}' | head -20
```

---

## Resource Groups and Permissions

| Resource | Resource Group | Notes |
|----------|----------------|-------|
| AKS Cluster | `rg-fund-rag` | GitHub Actions has Contributor access |
| App Service | `rg-fund-rag` | GitHub Actions has Contributor access |
| VNet/Subnets | `rg-fund-rag` | GitHub Actions has Contributor access |
| PostgreSQL | `aistartupstr` | **Different RG** - no GitHub Actions access |
| AI Search | `aistartupstr` | **Different RG** |
| Azure OpenAI | `aistartupstr` | **Different RG** |
| PII Container | `pii-ozguler` (ACI) | East US region |

This is why the health check workflow can monitor AKS but not PostgreSQL.

---

## Prompt Files for Replicating This Project

| Purpose | File Path |
|---------|-----------|
| Frontend Styling | `docs/STYLING_PROMPT.md` |
| Azure Infrastructure | Use plan file or recreate from CLAUDE.md |

These prompts can be used to set up similar projects with the same styling and infrastructure patterns.
