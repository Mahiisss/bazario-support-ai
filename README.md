<div align="center">

# 🛒 Bazario Support AI

**A production-grade multi-agent RAG system that resolves e-commerce customer support tickets using company policy — with zero hallucination tolerance.**

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![CrewAI](https://img.shields.io/badge/CrewAI-Multi--Agent-FF4B4B?style=flat)
![LangChain](https://img.shields.io/badge/LangChain-RAG-1C3C3C?style=flat)
![FAISS](https://img.shields.io/badge/FAISS-Vector%20Search-blue?style=flat)
![Groq](https://img.shields.io/badge/Groq-Llama%203.3%2070B-F55036?style=flat)
![React](https://img.shields.io/badge/React-Vite-61DAFB?style=flat&logo=react&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

[Features](#features) · [Architecture](#architecture) · [Anti-Hallucination](#anti-hallucination-design) · [Setup](#setup) · [Usage](#usage) · [Evaluation](#evaluation)

</div>

---

## What is this?

Bazario Support AI is an intelligent support resolution engine. Drop in a customer ticket — five specialized AI agents handle the rest. They triage the issue, retrieve the exact policy sections that apply, draft a cited resolution, verify every single claim, and escalate anything they can't confidently resolve.

No hallucinated refund amounts. No invented policies. Every claim in the final response is traceable to a specific policy document and chunk ID.

---

## Features

- **5-agent sequential pipeline** — Triage → Policy Retrieval → Resolution Writing → Compliance Review → Escalation
- **RAG-powered** — FAISS vector search over 25,000+ words of real policy documentation
- **Zero hallucination** — three independent layers block fabricated responses before they reach the customer
- **Full citations** — every claim references `[Source: filename | ID: chunk_id]`
- **React web UI** — clean dashboard with live agent progress tracking
- **REST API** — Flask backend with full ticket history and resolution storage
- **20-ticket evaluation suite** — standard, exception-heavy, conflict, and out-of-policy cases
- **Free to run** — powered by Groq (Llama 3.3 70B), no paid API key needed

---

## Architecture

```
Customer Ticket
       │
       ▼
┌──────────────────────────────────────┐
│           Triage Agent               │
│  Classifies issue type and urgency   │
│  Extracts key facts from order data  │
└────────────────┬─────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────┐
│       Policy Retriever Agent         │
│  Semantic search over FAISS index    │
│  Returns chunks with source + ID     │
└────────────────┬─────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────┐
│      Resolution Writer Agent         │
│  Drafts resolution from chunks ONLY  │
│  Every claim must include a citation │
└────────────────┬─────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────┐
│         Compliance Agent             │
│  Verifies citation coverage          │
│  Verdict: APPROVED / NEEDS REWRITE   │
│           / ESCALATE                 │
└────────────────┬─────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────┐
│         Escalation Agent             │
│  Handles edge cases & conflicts      │
│  Generates structured handoff report │
└──────────────────────────────────────┘
```

---

## Anti-Hallucination Design

Three independent layers prevent fabricated responses from ever reaching a customer.

**Layer 1 — Retrieval Grounding**
The Resolution Writer's context window contains only retrieved policy chunks. It has no pathway to use general knowledge for policy claims.

**Layer 2 — Mandatory Citation Format**
Every factual claim must reference `[Source: filename | ID: chunk_id]`. The system prompt explicitly forbids using knowledge not present in the retrieved chunks.

**Layer 3 — Independent Compliance Review**
The Compliance Agent reads the resolution cold — it doesn't know what the writer intended. It blocks the response if any claim is uncited, contradicts the source policy, or leaks customer PII.

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
| Backend API | Flask + Flask-CORS | REST API for the web UI |
| Frontend | React + Vite | Live agent progress dashboard |

---

## Policy Knowledge Base

| Document | Sections | Coverage |
|---|---|---|
| `returns_refunds.txt` | 10 | Standard returns, perishables, hygiene items, final sale, marketplace sellers |
| `cancellations.txt` | 10 | Pre/post-dispatch, subscriptions, bulk orders, marketplace |
| `shipping_delivery.txt` | 10 | Timelines, lost packages, transit damage, regional restrictions |
| `promotions.txt` | 10 | Coupons, cashback, bank offers, price match, abuse detection |
| `disputes.txt` | 10 | Damaged items, chargebacks, fraud, seller disputes, resolution timelines |

**Total: 50 sections · 25,000+ words · 64 indexed chunks**

---

## Project Structure

```
bazario-support-ai/
│
├── agents/
│   ├── triage_agent.py               # issue classification
│   ├── policy_retriever_agent.py     # FAISS search tool + retriever agent
│   ├── resolution_writer_agent.py    # citation-enforced resolution writing
│   ├── compliance_agent.py           # hallucination detection + verdict
│   └── escalation_agent.py           # human handoff report generator
│
├── core/
│   ├── ingestion.py                  # load policy .txt files with metadata
│   ├── chunker.py                    # recursive text splitting with chunk IDs
│   ├── embeddings.py                 # HuggingFace sentence-transformers
│   ├── vectorstore.py                # FAISS index build, save, load
│   └── retriever.py                  # similarity search + citation formatting
│
├── data/
│   └── policies/
│       ├── returns_refunds.txt
│       ├── cancellations.txt
│       ├── shipping_delivery.txt
│       ├── promotions.txt
│       └── disputes.txt
│
├── evaluation/
│   ├── test_tickets.json             # 20 test cases across 4 categories
│   └── run_eval.py                   # automated evaluation runner
│
├── frontend/                         # React web UI
│   └── src/
│       ├── App.jsx
│       └── components/
│           ├── TicketForm.jsx
│           ├── AgentProgress.jsx
│           ├── ResolutionView.jsx
│           └── HistorySidebar.jsx
│
├── config/
│   ├── settings.yaml                 # model, chunk size, retrieval config
│   └── prompts.yaml                  # all agent system prompts
│
├── api.py                            # Flask REST API
├── crew.py                           # CrewAI agent orchestration
├── tasks.py                          # task definitions and context chaining
├── models.py                         # Pydantic input/output schemas
└── main.py                           # CLI entry point
```

---

## Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- Free Groq API key from [console.groq.com](https://console.groq.com)

### 1. Clone the repository
```bash
git clone https://github.com/Mahiisss/bazario-support-ai
cd bazario-support-ai
```

### 2. Create and activate virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Add your Groq API key
```bash
# Windows PowerShell
Set-Content -Path .env -Value "GROQ_API_KEY=gsk_your_key_here"

# Mac/Linux
echo "GROQ_API_KEY=gsk_your_key_here" > .env
```

### 5. Run CLI only
```bash
python main.py
```

### 6. Run with Web UI

Terminal 1 — backend:
```bash
python api.py
```

Terminal 2 — frontend:
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
# run default test ticket
python main.py

# run custom ticket from JSON file
python main.py --ticket path/to/ticket.json

# suppress agent logs
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
| `POST` | `/resolve` | Submit a ticket for resolution |
| `GET` | `/history` | Get last 50 resolved tickets |
| `GET` | `/history/:id` | Get a specific ticket by ID |
| `GET` | `/health` | API health check |

---

## Evaluation

20 test tickets across 4 categories:

| Category | Count | Description |
|---|---|---|
| Standard | 8 | Clear policy match, unambiguous decision |
| Exception-heavy | 6 | Perishables, hygiene items, final sale, opened electronics |
| Conflict | 3 | Marketplace vs Bazario policy, regional restrictions |
| Not-in-policy | 3 | No coverage — requires escalation |

```bash
# run full evaluation suite
python evaluation/run_eval.py

# spot check specific cases
python evaluation/run_eval.py --cases TC-009 TC-015 TC-018
```

Results save to `evaluation/results/` with a markdown report.

**Metrics tracked:**
- Decision accuracy vs expected outcome
- Citation coverage rate
- Compliance pass rate (APPROVED on first review)
- Escalation rate
- Average resolution time per ticket

---

## Monitoring

Every run generates a CrewAI trace link in the terminal. Click it to see a visual timeline of all 5 agents — tool calls, LLM response times, and full outputs.

```
✅ Trace batch finalized
🔗 View here: https://app.crewai.com/crewai_plus/ephemeral_trace_batches/...
```

---

## Rate Limits

Groq free tier allows ~12,000 tokens/minute. Each pipeline run uses approximately 8,000–9,000 tokens. Wait 2–3 minutes between runs to avoid rate limit errors. The system includes automatic retry logic with up to 5 attempts.

For higher throughput, upgrade at [console.groq.com/settings/billing](https://console.groq.com/settings/billing).

---

## License

MIT