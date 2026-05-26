<div align="center">

# 🛒 Bazario Support AI

**A multi-agent RAG system that resolves e-commerce support tickets using verified order data and company policy.**

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![CrewAI](https://img.shields.io/badge/CrewAI-Multi--Agent-FF4B4B?style=flat)
![LangChain](https://img.shields.io/badge/LangChain-RAG-1C3C3C?style=flat)
![FAISS](https://img.shields.io/badge/FAISS-Vector%20Search-blue?style=flat)
![Groq](https://img.shields.io/badge/Groq-Llama%203.3%2070B-F55036?style=flat)
![React](https://img.shields.io/badge/React-Vite-61DAFB?style=flat&logo=react&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

</div>

---

## What is this?

Bazario Support AI takes a customer ticket and an order ID, looks up verified order details from a database, searches 25,000+ words of company policy using semantic search, drafts a cited resolution, runs it through an independent compliance review, and either approves it or escalates to a human agent.

No hallucinated refund amounts. No invented policies. Every claim is traceable to a specific policy document and chunk ID.

> **Note:** This is a functional prototype using a mock order database. Not yet production-ready for live deployment without a real database and persistent storage.

---

## How the pipeline works

```
Customer Ticket + Order ID
        │
        ▼
  Order Validation  ──── missing/invalid ──→  needs_info (no agents run)
        │
        ▼
   Triage Agent        classifies issue type and urgency
        │
        ▼
  Policy Retriever      semantic search over FAISS index, returns cited chunks
        │
        ▼
 Resolution Writer      drafts resolution using ONLY retrieved policy chunks
        │
        ▼
  Compliance Agent      APPROVED / NEEDS REWRITE / ESCALATE
        │
   ┌────┴────────────────┐
APPROVED           NEEDS REWRITE → rerun writer → re-review
   │                                      │
resolved                          APPROVED or ESCALATE
                                          │
                                  Escalation Agent  (only runs when needed)
                                  generates human handoff report
```

---

## Key features

- **Verified order lookup** — order details always fetched from database, never trusted from frontend
- **Conditional escalation** — escalation agent only runs when compliance says ESCALATE
- **Rewrite loop** — compliance sends drafts back to writer for correction before approving
- **Proper status mapping** — `resolved`, `escalated`, `needs_info`, `needs_review`, `error`
- **Structured JSON responses** — typed fields for status, verdict, customer response, decision, timestamp
- **Config-driven** — model, chunk size, compliance strictness all controlled via YAML files
- **React dashboard** — agent progress, order details, ticket history, proper status display

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Agents | CrewAI + Groq (Llama 3.3 70B) | Multi-agent orchestration + inference |
| RAG | LangChain + FAISS + all-MiniLM-L6-v2 | Policy retrieval + embeddings |
| Backend | Flask + Pydantic v2 | REST API + request validation |
| Frontend | React + Vite | Live agent progress dashboard |
| Config | YAML | Settings and agent prompts — no code changes needed |

---

## Policy knowledge base

| Document | Coverage |
|---|---|
| `returns_refunds.txt` | Standard returns, perishables, hygiene, final sale, marketplace |
| `cancellations.txt` | Pre/post-dispatch, subscriptions, bulk orders, marketplace |
| `shipping_delivery.txt` | Timelines, lost packages, transit damage, regional restrictions |
| `promotions.txt` | Coupons, cashback, bank offers, price match, abuse detection |
| `disputes.txt` | Damaged items, chargebacks, fraud, seller disputes |

**50 sections · 25,000+ words · 64 indexed chunks**

---

## Sample orders

| Order ID | Category | Status | Payment |
|---|---|---|---|
| ORD-2026-001 | Electronics | Delivered | UPI |
| ORD-2026-002 | Perishable | Delivered | Credit Card |
| ORD-2026-003 | Apparel | In Transit | COD |
| ORD-2026-004 | Hygiene | Delivered | Debit Card |
| ORD-2026-005 | Furniture | Delivered | Net Banking |
| ORD-2026-006 | Electronics | Cancelled | Credit Card |
| ORD-2026-007 | Books | Delivered | UPI |
| ORD-2026-008 | Electronics | Returned | Wallet |

---

## Setup

### Prerequisites
- Python 3.10+, Node.js 18+
- Free Groq API key from [console.groq.com](https://console.groq.com)

```bash
git clone https://github.com/Mahiisss/bazario-support-ai
cd bazario-support-ai
python -m venv venv && venv\Scripts\activate  # Windows
pip install -r requirements.txt
echo "GROQ_API_KEY=gsk_your_key_here" > .env
```

**Terminal 1 — backend:**
```bash
python api.py
```

**Terminal 2 — frontend:**
```bash
cd frontend && npm install && npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

---

## API endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/resolve` | Submit a ticket for resolution |
| `GET` | `/history` | Last 50 resolved tickets |
| `GET` | `/history/:id` | Get ticket by ID |
| `GET` | `/orders` | List mock orders |
| `GET` | `/orders/:id` | Get order by ID |
| `GET` | `/health` | Health check |

```json
// Request
{ "ticket_text": "My order arrived damaged. I want a refund.", "order_id": "ORD-2026-001" }

// Response
{
  "ticket_id": "TKT-ABC123",
  "status": "resolved",
  "verdict": "APPROVED",
  "customer_response": "Dear valued customer...",
  "order": { "order_id": "ORD-2026-001", "item_category": "electronics", ... },
  "timestamp": "2026-05-25T11:10:00"
}
```

---

## Known limitations

- Mock order database (`data/orders.json`) — not connected to a live order system
- Ticket history resets on server restart — needs a persistent database for production
- Groq free tier rate limits can cause delays — use multiple API keys or add credit
- Agent progress in UI is timer-based, not real-time streaming



