# Bazario Support AI — Technical Writeup

---

## Overview

Bazario Support AI is a multi-agent retrieval-augmented generation system designed to automate e-commerce customer support resolution. The system accepts a customer support ticket and order context, routes it through five specialized AI agents, and produces a policy-backed resolution with full citations without human intervention for standard cases.

The central design constraint is **no hallucination**. Every factual claim in a resolution must be traceable to a specific line in the policy knowledge base. This is enforced at three independent layers of the pipeline.

---

## Problem

E-commerce support teams handle thousands of tickets daily. The challenge is not just speed — it is consistency and accuracy. A support agent might correctly resolve a refund request for melted chocolates but incorrectly deny one the next day because they forgot the perishable item exception. Manual resolution is inconsistent by nature.

Automated resolution with a standard LLM is worse. Without grounding, a language model will confidently state refund timelines, policy exceptions, and eligibility rules that it invented — indistinguishable from real policy to the customer. This creates legal and trust risk.

The solution is a RAG pipeline where the LLM is explicitly restricted to retrieved content, with a separate compliance layer that independently verifies every claim before the response is sent.

---

## System Design

### Agent Pipeline

The system uses CrewAI to orchestrate five agents in a sequential pipeline. Each agent has a single responsibility and receives only the context it needs.

**Triage Agent**
Reads the raw ticket and order context. Outputs a structured classification: issue type (refund, cancellation, shipping, dispute, etc.), urgency level, key facts extracted from the order, and up to three clarifying questions if critical information is missing. This structured output becomes the input for the retrieval agent, which searches for specific policy categories rather than raw customer text. This improves retrieval precision significantly.

**Policy Retriever Agent**
Equipped with a custom FAISS search tool, this agent runs up to three targeted semantic searches against the policy knowledge base. It returns chunks with their source filename and chunk ID. The agent is explicitly instructed that it cannot state a policy rule from memory — if it is not in the retrieved chunks, it does not exist. This is the first hallucination prevention layer.

**Resolution Writer Agent**
Receives only the retrieved chunks from the previous agent. Writes the customer-facing resolution in a structured format: Classification, Clarifying Questions, Decision, Rationale, Citations, Customer Response Draft, and Internal Notes. A hard constraint in the system prompt mandates `[Source: filename | ID: chunk_id]` for every factual claim. The agent is forbidden from using general knowledge for policy statements.

**Compliance Agent**
This agent operates independently. It receives the draft resolution and checks it against three criteria: citation coverage (every claim has a citation), decision-policy alignment (the decision matches the cited policy), and conflict detection (no contradictions between cited sources). It outputs APPROVED, NEEDS REWRITE, or ESCALATE with specific reasons. Crucially, this agent did not write the resolution — it reviews it fresh, which makes it a more reliable hallucination detector than asking the writer to self-check.

**Escalation Agent**
Handles tickets where compliance returns NEEDS REWRITE or ESCALATE, or where the policy knowledge base has no coverage. Produces a structured handoff report for the human support team: why the ticket is being escalated, what was attempted, what policy gaps exist, recommended next steps, and a draft customer message explaining the delay.

### RAG Implementation

**Knowledge Base**
Five policy documents were created covering all major e-commerce support categories. The corpus totals over 25,000 words across 50+ sections. Documents cover standard cases alongside the edge cases that matter most for evaluation: perishable items, hygiene products, final sale exceptions, marketplace seller rules, regional shipping restrictions, and out-of-policy requests like emotional distress claims.

**Chunking**
Documents are split using `RecursiveCharacterTextSplitter` with chunk size 500 and overlap 100. The 500 character size was chosen to capture complete policy clauses without losing context at boundaries. The overlap ensures that rules split across a boundary appear in at least one complete chunk. Every chunk is tagged with a unique `chunk_id` composed of the source filename and a zero-padded index, enabling precise citation tracing.

**Embeddings**
`sentence-transformers/all-MiniLM-L6-v2` produces 384-dimensional embeddings with cosine normalization enabled. This model was chosen for its strong semantic performance on short passages, low inference cost, and ability to run entirely on CPU without a GPU requirement.

**Vector Store**
FAISS was chosen over alternatives like ChromaDB for three reasons: it requires no server process, it is significantly faster for read heavy workloads with a fixed corpus, and it persists cleanly to disk. The index is built once on startup and cached. Subsequent runs load the cached index in under a second.

**Retrieval Strategy**
Rather than passing the raw ticket text directly to the search tool, the Triage Agent's structured output is used to generate focused search queries. For example, a ticket about melted chocolates generates queries like "perishable item refund policy" and "damaged goods return waiver" rather than the raw customer complaint. This improves both precision and recall.

---

## Hallucination Prevention

Three independent controls work at different stages of the pipeline:

**Retrieval Grounding (pre-generation)**
The Resolution Writer's context window is constructed to contain only retrieved policy chunks. There is no system message that allows it to draw on general knowledge for policy claims. The only way a policy rule enters the resolution is if it was retrieved from the FAISS index.

**Citation Enforcement (generation)**
The system prompt mandates a specific citation format for every factual claim. This serves two purposes: it forces the model to identify which retrieved chunk supports each claim (catching cases where it might drift), and it produces machine-readable citations that the compliance agent can verify automatically.

**Compliance Gating (post-generation)**
The Compliance Agent is a separate LLM call with no memory of the Resolution Writer's process. It receives the draft resolution and the retrieved chunks, then independently checks whether every cited claim actually appears in the cited source. This separation prevents the writer from rationalizing its own hallucinations. A resolution that fails compliance is either rewritten or escalated — it does not reach the customer.

---

## Evaluation

The evaluation set contains 20 tickets designed to stress-test the pipeline across the scenarios that matter most:

**Standard cases (8 tickets)** cover the most common support scenarios with clear policy matches. These establish the baseline accuracy of the retrieval and resolution pipeline.

**Exception-heavy cases (6 tickets)** test the system's ability to identify and correctly apply policy exceptions. Examples include perishable items arriving damaged, hygiene products opened before a defect was noticed, electronics returned after the standard window, and items purchased during a final sale event.

**Conflict cases (3 tickets)** involve genuine policy tensions: a marketplace seller's return policy conflicting with Bazario's standard terms, a customer in a region with shipping restrictions, and an order fulfilled jointly by Bazario and a marketplace seller. These test whether the compliance agent correctly flags conflicts rather than silently resolving them in favor of one policy.

**Not-in-policy cases (3 tickets)** cover requests with no policy coverage at all — a customer asking for compensation for emotional distress, a request to match a competitor's price, and an ambiguous ticket with insufficient information to classify. These test whether the system correctly escalates rather than fabricating a policy-based justification.

---

## Design Decisions

**Why five agents instead of one?**
A single LLM call combining all five responsibilities consistently produces lower quality output than separating them. The compliance review in particular benefits from being a separate agent with no prior context — it genuinely reviews the resolution rather than confirming the writer's intent. The triage stage also meaningfully improves retrieval by producing focused search queries rather than passing raw customer text to the vector store.

**Why CrewAI?**
CrewAI provides clean sequential task chaining with explicit context passing between agents. It also generates execution traces that make debugging multi-agent flows significantly easier than raw LangChain agent loops.

**Why Groq?**
Groq's inference speed is substantially faster than hosted alternatives at equivalent model quality, and the free tier is sufficient for development and evaluation. Llama 3.3 70B performs well on structured output tasks like classification, citation-aware writing, and compliance review.

**Why FAISS over a managed vector database?**
The policy corpus is fixed and small enough that a managed database adds complexity without benefit. FAISS builds in under a second, loads from disk instantly, and requires no running service. The right tool for the scale.

---

## Limitations

**Rate limits on free tier**
Groq's free tier enforces a 12,000 token-per-minute limit. Each pipeline run consumes approximately 8,000-9,000 tokens, so consecutive runs hit the limit. Automatic retry logic handles this, but it adds latency. The fix is either waiting between runs or upgrading to a paid tier.

**Synthetic policy corpus**
The policy knowledge base was created for this project. In a production deployment, it would be replaced with real company policy documents, which may require tuning the chunking strategy for longer or more complex structures.

**No streaming**
The Flask API returns the full resolution after all five agents complete. A production system would use server-sent events or WebSockets to stream each agent's output to the UI in real time, significantly improving perceived responsiveness.

**Single-language support**
The current system handles English tickets only. Extending to Hindi and other Indian languages would require multilingual embeddings and LLM prompts.

---

## Tech Stack

| Component | Technology |
|---|---|
| Agent Orchestration | CrewAI |
| LLM | Groq — Llama 3.3 70B Versatile |
| RAG Framework | LangChain + LangChain Community |
| Vector Store | FAISS (CPU) |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 |
| Data Validation | Pydantic v2 |
| Backend API | Flask + Flask-CORS |
| Frontend | React 18 + Vite |
| Language | Python 3.12 |