<div align="center">

# Bazario Support AI

**A production grade multi-agent RAG system that resolves e-commerce customer support tickets using company policy with zero hallucination tolerance.**

[Features](#features) · [Architecture](#architecture) · [Setup](#setup) · [Usage](#usage) · [Evaluation](#evaluation)

</div>

---

## What is this?

Bazario Support AI is an intelligent support resolution engine. When a customer submits a ticket, five specialized AI agents work in sequence triaging the issue, retrieving relevant policy, drafting a resolution, verifying every citation, and escalating edge cases all without a human in the loop.

Every resolution is grounded in a real policy knowledge base. No hallucinated rules. No invented refund amounts. Every claim is cited.

---

## Features

- **5-agent pipeline** — Triage → Policy Retrieval → Resolution Writing → Compliance Review → Escalation
- **RAG-powered** — FAISS vector search over 25,000+ words of policy documentation
- **Zero hallucination** — three independent layers prevent fabricated responses
- **Full citations** — every claim references `[Source: filename | ID: chunk_id]`
- **Web UI** — clean React dashboard with live agent progress tracking
- **REST API** — Flask backend with ticket history and resolution storage
- **20-ticket evaluation suite** — covers standard, exception, conflict, and out-of-policy cases
- **Free to run** — powered by Groq (Llama 3.3 70B), no paid API needed

---

## Architecture

```
Customer Ticket
       │
       ▼
┌──────────────────┐
│   Triage Agent   │  Classifies issue type and urgency
│                  │  Extracts key facts from order context
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Policy Retriever │  Runs semantic search over FAISS index
│     Agent        │  Returns chunks with source + chunk ID
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   Resolution     │  Writes resolution using ONLY retrieved chunks
│   Writer Agent   │  Every claim must have a citation
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Compliance      │  Reviews citation coverage and policy alignment
│     Agent        │  Verdict: APPROVED / NEEDS REWRITE / ESCALATE
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Escalation      │  Handles edge cases and out-of-policy tickets
│     Agent        │  Prepares structured human handoff report
└──────────────────┘
```

---

## Anti-Hallucination Design

Three independent layers prevent fabricated responses:

**Layer 1 — Retrieval Grounding**
The Resolution Writer's context window contains only retrieved policy chunks. It has no pathway to use general knowledge for policy claims.

**Layer 2 — Mandatory Citation Format**
Every factual claim must reference `[Source: filename | ID: chunk_id]`. The system prompt explicitly forbids using knowledge not present in the retrieved chunks.

**Layer 3 — Independent Compliance Review**
The Compliance Agent reads the resolution fresh — it doesn't know what the writer intended. It blocks the response if any claim is uncited, contradicts the source, or reveals customer PII.

---

## Project Structure

```
bazario-support-ai/
│
├── agents/
│   ├── triage_agent.py              # issue classification
│   ├── policy_retriever_agent.py    # FAISS search tool + retriever agent
│   ├── resolution_writer_agent.py   # citation-enforced resolution writing
│   ├── compliance_agent.py          # hallucination detection + verdict
│   └── escalation_agent.py          # human handoff report generator
│
├── core/
│   ├── ingestion.py                 # load policy .txt files with metadata
│   ├── chunker.py                   # recursive text splitting with chunk IDs
│   ├── embeddings.py                # HuggingFace sentence-transformers
│   ├── vectorstore.py               # FAISS index build, save, load
│   └── retriever.py                 # similarity search + citation formatting
│
├── data/
│   ├── policies/
│   │   ├── returns_refunds.txt      # 10 sections
│   │   ├── cancellations.txt        # 10 sections
│   │   ├── shipping_delivery.txt    # 10 sections
│   │   ├── promotions.txt           # 10 sections
│   │   └── disputes.txt             # 10 sections
│   └── faiss_index/                 # auto-generated on first run
│
├── evaluation/
│   ├── test_tickets.json            # 20 test cases across 4 categories
│   └── run_eval.py                  # automated evaluation runner
│
├── frontend/                        # React web UI
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── components/
│   │       ├── TicketForm.jsx
│   │       ├── AgentProgress.jsx
│   │       ├── ResolutionView.jsx
│   │       └── HistorySidebar.jsx
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── config/
│   ├── settings.yaml                # model, chunk size, retrieval config
│   └── prompts.yaml                 # all agent system prompts
│
├── outputs/
│   ├── resolutions/                 # saved ticket resolutions (.txt)
│   └── history.json                 # ticket history for UI
│
├── api.py                           # Flask REST API
├── crew.py                          # CrewAI agent orchestration
├── tasks.py                         # task definitions and context chaining
├── models.py                        # Pydantic input/output schemas
├── main.py                          # CLI entry point
├── requirements.txt
└── .env
```

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Agent Orchestration | CrewAI | Multi-agent pipeline management |
| LLM | Groq — Llama 3.3 70B | Fast, free inference |
| RAG Framework | LangChain | Document loading, chunking, retrieval |
| Vector Store | FAISS (CPU) | Semantic similarity search |
| Embeddings | all-MiniLM-L6-v2 | 384-dim sentence embeddings |
| Data Validation | Pydantic v2 | Input/output schema enforcement |
| Backend API | Flask + Flask-CORS | REST API for web UI |
| Frontend | React + Vite | Web dashboard |

---

## Policy Knowledge Base

| Document | Sections | Coverage |
|---|---|---|
| returns_refunds.txt | 10 | Standard returns, perishables, hygiene items, final sale, marketplace sellers |
| cancellations.txt | 10 | Pre/post-dispatch, subscriptions, bulk orders, marketplace |
| shipping_delivery.txt | 10 | Timelines, lost packages, transit damage, regional restrictions |
| promotions.txt | 10 | Coupons, cashback, bank offers, price match, abuse detection |
| disputes.txt | 10 | Damaged items, chargebacks, fraud, seller disputes, resolution timelines |

**Total: 50+ sections · 25,000+ words · 64 indexed chunks**

---

## Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- Free Groq API key from [console.groq.com](https://console.groq.com)

### 1. Clone the repository
```bash
git clone https://github.com/yourname/bazario-support-ai
cd bazario-support-ai
```

### 2. Create virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment
```bash
# Windows PowerShell
Set-Content -Path .env -Value "GROQ_API_KEY=gsk_your_key_here"

# Mac/Linux
echo "GROQ_API_KEY=gsk_your_key_here" > .env
```

### 5. Run CLI (no UI)
```bash
python main.py
```

### 6. Run with Web UI

Terminal 1 — start backend:
```bash
python api.py
```

Terminal 2 — start frontend:
```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

---

## Usage

### CLI

```bash
# default test ticket
python main.py

# custom ticket from JSON
python main.py --ticket path/to/ticket.json

# quiet mode (suppress agent logs)
python main.py --quiet
```

### Ticket JSON format

```json
{
  "ticket_id": "TC-001",
  "ticket_text": "My order arrived damaged. I want a full refund.",
  "order": {
    "order_id": "ORD-2026-001",
    "order_date": "2026-03-20",
    "delivery_date": "2026-03-25",
    "item_category": "electronics",
    "fulfillment_type": "first-party",
    "shipping_region": "India",
    "order_status": "delivered",
    "payment_method": "UPI"
  }
}
```

### API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/resolve` | Submit a ticket for resolution |
| GET | `/history` | Get last 50 resolved tickets |
| GET | `/history/:id` | Get a specific ticket by ID |
| GET | `/health` | API health check |

---

## Evaluation

20 test tickets across 4 categories:

| Category | Count | Description |
|---|---|---|
| Standard | 8 | Clear policy match, unambiguous decision |
| Exception-heavy | 6 | Perishables, hygiene, final sale, opened electronics |
| Conflict | 3 | Marketplace vs Bazario policy, regional restrictions |
| Not-in-policy | 3 | No coverage — requires escalation |

```bash
# run full evaluation suite
python evaluation/run_eval.py

# spot check specific cases
python evaluation/run_eval.py --cases TC-009 TC-015 TC-018
```

Results save to `evaluation/results/` with a markdown report.

### Metrics tracked
- Decision accuracy vs expected outcome
- Citation coverage rate
- Compliance pass rate (APPROVED on first review)
- Escalation rate
- Average resolution time per ticket

---

## Monitoring

Every run generates a CrewAI trace link in the terminal output. Open it in your browser to see a visual timeline of all 5 agents, their tool calls, LLM response times, and outputs.

```
Trace Batch Finalization
✅ Trace batch finalized
🔗 View here: https://app.crewai.com/crewai_plus/ephemeral_trace_batches/...
```

---

## Rate Limits

Groq free tier allows 12,000 tokens per minute. Each pipeline run uses approximately 8,000-9,000 tokens. To avoid rate limit errors, wait 2-3 minutes between runs. The system includes automatic retry logic with up to 5 attempts.

For higher throughput, upgrade to Groq Dev tier at [console.groq.com/settings/billing](https://console.groq.com/settings/billing).

