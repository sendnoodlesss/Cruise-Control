# 🚀 Cruise Control

> AI-powered outbound sales automation — from ICP definition to personalized email drafts, fully orchestrated.

---

## 📋 Project Summary 

Cruise Control is a full-stack outbound sales automation platform that transforms an Ideal Customer Profile (ICP) into verified, personalized email drafts — ready to send. Users define their target market, and a 6-agent AI pipeline handles the rest: scraping company data, enriching contacts, verifying emails, researching prospects, generating personalized copy, and surfacing drafts for human review. Built on FastAPI + React with MongoDB Atlas persistence, the system routes intelligently across LLM providers (OpenAI, Anthropic, Gemini) using a unified llm_router. Phase 1 ships with mocked data and manual review. Phase 2 wires live APIs and Gmail OAuth.

---

## 🧰 Tools & Tech

| Layer | Technology |
|---|---|
| **Frontend** | React 18, React Router v6, Axios, TailwindCSS |
| **Backend** | Python 3.11, FastAPI, Uvicorn, Motor (async MongoDB) |
| **Database** | MongoDB Atlas (cloud) / MongoDB local (dev fallback) |
| **AI / LLM** | OpenAI GPT-4o, Anthropic Claude 3.5, Google Gemini 1.5 |
| **LLM Routing** | Custom `llm_router.py` — model selection by task/cost/speed |
| **Web Scraping** | Apify (Apollo, LinkedIn actors) |
| **Email Verification** | Hunter.io API |
| **Email Sending** | Gmail OAuth2 (Phase 2) |
| **Auth** | MongoDB Atlas UI (no app-level auth in MVP) |
| **Deployment** | Local dev / Railway or Render (planned) |
| **Version Control** | Git + GitHub |

---

## 🏗️ Architecture
┌─────────────────────────────────────────────────────────┐
│ FRONTEND (React) │
│ Dashboard → Pathways → Run Progress → Results → │
│ Email Review → API Settings → Integrations │
└───────────────────────┬─────────────────────────────────┘
│ HTTP / REST (Axios)
┌───────────────────────▼─────────────────────────────────┐
│ BACKEND (FastAPI) │
│ │
│ /api/pathways /api/runs /api/emails │
│ /api/agents /api/settings /health │
│ │
│ ┌──────────────────────────────────────────────┐ │
│ │ AGENT ORCHESTRATOR │ │
│ │ │ │
│ │ Agent 1: ICP Scraper (Apify) │ │
│ │ Agent 2: Contact Enricher (Apify/Apollo) │ │
│ │ Agent 3: Email Verifier (Hunter.io) │ │
│ │ Agent 4: Prospect Researcher (LLM) │ │
│ │ Agent 5: Email Copywriter (LLM) │ │
│ │ Agent 6: Review Queuer (MongoDB) │ │
│ └──────────────┬───────────────────────────────┘ │
│ │ │
│ ┌──────────────▼───────────────────────────────┐ │
│ │ LLM ROUTER │ │
│ │ Routes by: task type, cost, speed, fallback │ │
│ │ Providers: OpenAI | Anthropic | Gemini │ │
│ └──────────────────────────────────────────────┘ │
└───────────────────────┬─────────────────────────────────┘
│ Motor (async)
┌───────────────────────▼─────────────────────────────────┐
│ MongoDB Atlas │
│ Collections: pathways | runs | contacts | emails │
└─────────────────────────────────────────────────────────┘

## 🗂️ Repository Structure
cruise-control/
├── backend/
│ ├── main.py # FastAPI app entry point
│ ├── database.py # Motor MongoDB client
│ ├── llm_router.py # Multi-provider LLM routing
│ ├── models/
│ │ ├── pathway.py # Pathway Pydantic model
│ │ ├── run.py # Run model
│ │ ├── contact.py # Contact model
│ │ └── email_draft.py # EmailDraft model
│ ├── routers/
│ │ ├── pathways.py # CRUD for pathways
│ │ ├── runs.py # Trigger + monitor runs
│ │ ├── emails.py # Draft review endpoints
│ │ └── settings.py # API key management
│ ├── agents/
│ │ ├── orchestrator.py # Run all 6 agents in sequence
│ │ ├── scraper.py # Agent 1: Apify ICP scraper
│ │ ├── enricher.py # Agent 2: Contact enrichment
│ │ ├── verifier.py # Agent 3: Hunter.io email verify
│ │ ├── researcher.py # Agent 4: LLM prospect research
│ │ ├── copywriter.py # Agent 5: LLM email drafts
│ │ └── queuer.py # Agent 6: Save to MongoDB
│ └── requirements.txt
├── frontend/
│ ├── public/
│ ├── src/
│ │ ├── App.js # React Router config
│ │ ├── components/
│ │ │ └── Shell.jsx # Nav sidebar + layout
│ │ ├── pages/
│ │ │ ├── Dashboard.jsx
│ │ │ ├── Pathways.jsx
│ │ │ ├── RunProgress.jsx
│ │ │ ├── PathwayResults.jsx
│ │ │ ├── EmailReview.jsx
│ │ │ ├── ApiSettings.jsx
│ │ │ └── Integrations.jsx
│ │ └── index.js
│ ├── package.json
│ └── tailwind.config.js
├── docs/
│ └── architecture.png # Architecture diagram export
├── .env.example # Safe env template (no secrets)
├── .gitignore
├── README.md
└── LICENCE


---

## ⚙️ Setup Instructions

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/cruise-control.git
cd cruise-control
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

Create your `.env` file (copy from `.env.example`):

```bash
cp .env.example .env
```

Start the backend:

```bash
uvicorn main:app --reload --port 8000
```

Backend health check: `http://localhost:8000/health`

### 3. Frontend Setup

```bash
cd frontend
npm install
npm start
```

Frontend runs at: `http://localhost:3000`

---

## 🔐 Environment Variables (`.env.example`)

```env
# MongoDB
MONGO_URL=mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/cruise_control?retryWrites=true&w=majority

# LLM Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AIza...

# Scraping & Enrichment
APIFY_API_TOKEN=apify_api_...
HUNTER_API_KEY=...

# Gmail OAuth (Phase 2)
GMAIL_CLIENT_ID=
GMAIL_CLIENT_SECRET=
GMAIL_REFRESH_TOKEN=
```

> ⚠️ Never commit your real `.env` file. It is listed in `.gitignore`.

---

## 🔄 Agent Pipeline (Technical Details)

The orchestrator runs 6 agents sequentially per pathway run. Agent 1 uses Apify to scrape companies matching the ICP. Agent 2 enriches each company with contact data via Apollo. Agent 3 verifies email deliverability via Hunter.io. Agent 4 uses the LLM router to research each prospect (news, LinkedIn signals). Agent 5 generates a personalized email draft using researched context. Agent 6 saves all drafts to MongoDB for human review. The LLM router selects the optimal provider per task — Gemini for fast research, Claude for copy, GPT-4o as fallback — balancing cost, speed, and quality automatically.

---

## 🧪 Testing the MVP (Phase 1 — Mocked)

1. Start backend: `uvicorn main:app --reload`
2. Start frontend: `npm start`
3. Navigate to `Dashboard` → click **New Pathway**
4. Fill ICP form → Save
5. Click **Run Agents** on the pathway card
6. Watch `Run Progress` page for agent status updates
7. When complete, navigate to `Email Review` to approve/edit drafts

For Phase 1, agent outputs are mocked — no real API calls are made unless keys are configured.

---

## 🗺️ Roadmap

| Phase | Status | Description |
|---|---|---|
| Phase 1 | ✅ MVP | Mocked agent pipeline, full UI, MongoDB persistence |
| Phase 2 | 🔄 In Progress | Live Apify + Hunter + LLM integration |
| Phase 3 | 📋 Planned | Gmail OAuth send, analytics dashboard, multi-user auth |

---

## 🚀 Push to GitHub

```bash
# From project root
git init
git add .
git commit -m "feat: initial Cruise Control MVP"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/cruise-control.git
git push -u origin main
```

---

## 📄 Licence

MIT — see `LICENCE` file.

