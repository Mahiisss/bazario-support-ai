<div align="center">

# 🛒 Bazario Support AI

### A multi-agent RAG system that resolves e-commerce support tickets using verified order data, semantic policy search, and citation-enforced AI responses.
Policy-aware AI support system built with CrewAI, RAG, compliance review, and PostgreSQL persistence.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![CrewAI](https://img.shields.io/badge/CrewAI-Multi--Agent-FF4B4B?style=flat)](https://crewai.com)
[![LangChain](https://img.shields.io/badge/LangChain-RAG-1C3C3C?style=flat)](https://langchain.com)
[![FAISS](https://img.shields.io/badge/FAISS-Vector%20Search-blue?style=flat)](https://faiss.ai)
[![Groq](https://img.shields.io/badge/Groq-Llama%203.3%2070B-F55036?style=flat)](https://groq.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-336791?style=flat&logo=postgresql&logoColor=white)](https://supabase.com)
[![React](https://img.shields.io/badge/React-Vite-61DAFB?style=flat&logo=react&logoColor=white)](https://vitejs.dev)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat)](LICENSE)

**[What It Does](#what-it-does) · [Pipeline](#pipeline) · [Tech Stack](#tech-stack) · [Setup](#setup) · [API](#api)**

</div>

---

## What It Does

Bazario Support AI takes a customer support ticket and an order ID, looks up the verified order record, searches 25,000+ words of company policy using semantic vector search, drafts a fully cited resolution, and runs it through an independent compliance review before returning anything to the customer.

Every factual claim in the response is traceable to a specific policy file and chunk ID. The system never trusts frontend-provided order data — it always fetches from the backend. If compliance isn't satisfied, the writer revises. If it still can't resolve, a structured escalation report goes to a human agent. Every ticket is persisted to PostgreSQL so history survives restarts.

> **Note:** This is a working prototype. Order data uses a mock database; ticket history is persisted in PostgreSQL (Supabase).

---

## Pipeline

```
Customer Ticket + Order ID
        │
        ▼
  ┌──────────────────┐
  │ Order Validation │  ── not found ──▶  needs_info (pipeline stops)
  └────────┬─────────┘
           │
           ▼
  ┌──────────────────┐
  │   Triage Agent   │  classifies issue type and urgency
  └────────┬─────────┘
           │
           ▼
  ┌──────────────────────┐
  │   Policy Retriever   │  semantic search · returns cited policy chunks
  └────────┬─────────────┘
           │
           ▼
  ┌──────────────────────┐
  │   Resolution Writer  │  drafts response using retrieved chunks only
  └────────┬─────────────┘
           │
           ▼
  ┌──────────────────────┐
  │   Compliance Agent   │  verifies every claim against citations
  └────────┬─────────────┘
           │
    ┌──────┴──────────────────┐
    │                         │
  APPROVED              NEEDS REWRITE ──▶ writer reruns ──▶ compliance re-reviews
    │                                                               │
  resolved                                                    ESCALATE
                                                                   │
                                                    ┌──────────────────────┐
                                                    │   Escalation Agent   │
                                                    │  human handoff report│
                                                    └──────────────────────┘
                                                          escalated

  Every result is saved to PostgreSQL ▼
```

---

## What Makes It Different

| Feature | How It Works |
|---|---|
| **Verified order data** | Order ID looked up from backend — frontend can't inject fake data |
| **Citation-enforced responses** | Writer uses retrieved chunks only · every claim must reference `[Source: file \| ID: chunk_id]` |
| **Independent compliance gate** | Separate agent reads the draft cold and blocks uncited or invented policy |
| **Rewrite loop** | NEEDS REWRITE sends the draft back to the writer for correction before compliance re-reviews |
| **Conditional escalation** | Escalation agent only runs when compliance explicitly returns ESCALATE |
| **Accurate status mapping** | `resolved` · `escalated` · `needs_info` · `needs_review` · `error` — never marks escalation as resolved |
| **Persistent history** | Every ticket saved to PostgreSQL (Supabase) — survives server restarts |
| **API key rotation** | Rotates across multiple Groq keys on rate limit to maximize free-tier throughput |
| **Config-driven** | Model, chunk size, agent prompts — all in YAML, zero code changes needed |

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Agent Orchestration | CrewAI | Multi-agent sequential pipeline |
| LLM | Groq — Llama 3.3 70B | Fast inference |
| RAG | LangChain + FAISS | Document chunking, embedding, retrieval |
| Embeddings | all-MiniLM-L6-v2 | 384-dim sentence embeddings (local, no API) |
| Backend | Flask + Pydantic v2 | REST API + request validation |
| Database | PostgreSQL (Supabase) | Persistent ticket history |
| Frontend | React + Vite | Agent progress dashboard |
| Config | YAML | Settings and agent prompts |

---

## Policy Knowledge Base

| File | Coverage |
|---|---|
| `returns_refunds.txt` | Standard returns, perishables, hygiene, final sale, marketplace sellers |
| `cancellations.txt` | Pre/post-dispatch, subscriptions, bulk orders, marketplace |
| `shipping_delivery.txt` | Timelines, lost packages, transit damage, regional restrictions |
| `promotions.txt` | Coupons, cashback, bank offers, price match, abuse detection |
| `disputes.txt` | Damaged items, chargebacks, fraud, seller disputes, resolution timelines |

**50 sections · 25,000+ words · 64 indexed chunks**

---

## Project Structure

```
bazario-support-ai/
│
├── agents/                       # the five specialized agents
│   ├── triage_agent.py
│   ├── policy_retriever_agent.py
│   ├── resolution_writer_agent.py
│   ├── compliance_agent.py       # loads prompts from config/prompts.yaml
│   └── escalation_agent.py
│
├── core/                         # RAG pipeline
│   ├── ingestion.py              # load policy docs
│   ├── chunker.py                # recursive chunking (config-driven)
│   ├── embeddings.py             # sentence-transformers (config-driven)
│   ├── vectorstore.py            # FAISS build / save / load
│   └── retriever.py              # similarity search + citation formatting
│
├── config/
│   ├── config.py                 # loads settings.yaml into a dataclass
│   ├── settings.yaml             # model, chunk size, retrieval config
│   └── prompts.yaml              # all agent system prompts
│
├── data/
│   ├── orders.json               # mock order database
│   ├── faiss_index/              # built on first run
│   └── policies/                 # 5 policy .txt files
│
├── evaluation/
│   ├── run_eval.py               # structured evaluation runner
│   └── test_tickets.json         # 20 test cases across 4 categories
│
├── frontend/                     # React + Vite dashboard
│   └── src/
│       ├── App.jsx               # loads history from DB on mount
│       └── components/
│           ├── TicketForm.jsx
│           ├── AgentProgress.jsx
│           ├── ResolutionView.jsx
│           └── HistorySidebar.jsx
│
├── api.py                        # Flask REST API
├── crew.py                       # CrewAI orchestration + key rotation
├── tasks.py                      # task definitions + rewrite/escalation tasks
├── models.py                     # Pydantic schemas (TicketInput, ResolutionResult)
├── database.py                   # PostgreSQL persistence layer
└── main.py                       # CLI entry point
```

---

## Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- Free Groq API key → [console.groq.com](https://console.groq.com)
- Free Supabase project → [supabase.com](https://supabase.com)

### Run locally

```bash
# 1. Clone
git clone https://github.com/Mahiisss/bazario-support-ai
cd bazario-support-ai

# 2. Virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Environment variables
cp .env.example .env
# Add your GROQ_API_KEY and DATABASE_URL to .env

# 5. Start backend
python api.py

# 6. Start frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### Environment variables

```env
# Groq — single key
GROQ_API_KEY=gsk_...

# Or multiple keys for rate-limit rotation (optional)
GROQ_API_KEY_1=gsk_...
GROQ_API_KEY_2=gsk_...

# Supabase PostgreSQL connection string
DATABASE_URL=postgresql://postgres.xxxx:password@aws-xxx.pooler.supabase.com:5432/postgres
```

---

## Sample Orders

Use these order IDs to test different scenarios:

| Order ID | Category | Status | Fulfillment | Payment |
|---|---|---|---|---|
| ORD-2026-001 | Electronics | Delivered | First-party | UPI |
| ORD-2026-002 | Perishable | Delivered | First-party | Credit Card |
| ORD-2026-003 | Apparel | In Transit | Marketplace | COD |
| ORD-2026-004 | Hygiene | Delivered | First-party | Debit Card |
| ORD-2026-005 | Furniture | Delivered | First-party | Net Banking |
| ORD-2026-006 | Electronics | Cancelled | Marketplace | Credit Card |
| ORD-2026-007 | Books | Delivered | First-party | UPI |
| ORD-2026-008 | Electronics | Returned | First-party | Wallet |

---

## API

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/resolve` | Submit a ticket for resolution |
| `GET` | `/history` | Last 50 resolved tickets (from PostgreSQL) |
| `GET` | `/history/:id` | Get ticket by ID |
| `GET` | `/orders` | List all sample orders |
| `GET` | `/orders/:id` | Get order by ID |
| `GET` | `/health` | Health check |

**Request**
```json
{
  "ticket_text": "My laptop arrived with a cracked screen. I want a refund.",
  "order_id": "ORD-2026-001"
}
```

**Response**
```json
{
  "ticket_id": "TKT-A1B2C3D4",
  "status": "resolved",
  "verdict": "APPROVED",
  "decision": "Full refund approved — item confirmed damaged on arrival.",
  "customer_response": "Dear valued customer, thank you for reporting...",
  "order": {
    "order_id": "ORD-2026-001",
    "item_category": "electronics",
    "order_status": "delivered",
    "payment_method": "UPI"
  },
  "timestamp": "2026-05-25T16:37:00"
}
```

**Status values**

| Status | Meaning |
|---|---|
| `resolved` | Compliance approved — response sent |
| `escalated` | Escalation report generated for human agent |
| `needs_review` | Compliance flagged unresolvable issues |
| `needs_info` | Order ID missing or not found |
| `error` | Unexpected backend error |

---

## Configuration

All settings live in `config/settings.yaml` — change the model, chunk size, or retrieval parameters without touching Python:

```yaml
llm:
  model: "groq/llama-3.3-70b-versatile"
  temperature: 0.1

vectorstore:
  chunk_size: 500
  chunk_overlap: 100

retrieval:
  top_k: 3
```

Agent behavior lives in `config/prompts.yaml` — tune compliance strictness, triage categories, or response format without touching agent code.

---

## Evaluation

A 20-case test suite spanning four categories — standard, exception-heavy, policy-conflict, and out-of-policy:

```bash
python evaluation/run_eval.py

# spot check specific cases
python evaluation/run_eval.py --cases TC-001 TC-009 TC-015
```

Results are evaluated against structured `ResolutionResult` fields (status, verdict, decision) — not fragile keyword matching — and saved as a grouped markdown report.

---

## Known Limitations

- Order lookup uses a mock JSON file (`data/orders.json`), not a live order management system — ticket history itself is persisted in PostgreSQL
- Agent progress in the UI is timer-based, not real-time streaming
- Groq free tier rate limits can slow back-to-back requests — mitigated with key rotation

---


