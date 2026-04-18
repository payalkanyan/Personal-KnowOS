# Personal Knowledge OS — Full Architecture

A production-grade system that ingests everything you read and write, builds a knowledge graph over it, and lets you query your own mind with hybrid RAG retrieval.

---

## Table of Contents

1. [Ingestion Layer](#1-ingestion-layer)
2. [Processing Pipeline](#2-processing-pipeline)
3. [Memory Architecture](#3-memory-architecture)
4. [Query & Retrieval](#4-query--retrieval)
5. [Design Decisions](#5-design-decisions)

---

## 1. Ingestion Layer

Chrome Extension  + Desktop App: For now focusing on Chrome Extension.
---

### Chrome Extension

**What it captures:**
- Page content as you browse (reader-mode cleaned HTML)
- Selected text and highlights
- Tab metadata (URL, title, time spent)
- YouTube transcripts via transcript API
- PDFs opened in the browser

**How it works:**

A content script injects into every page. On tab close or user trigger, it extracts cleaned text via `Readability.js`, then POSTs to your local FastAPI server on port 8000.

```
chrome.tabs API + content scripts + background service worker
```

**Smart triggers — don't capture everything:**
- Time-on-page threshold: 30 seconds minimum
- Scroll depth: 40% minimum
- Or explicit "save this" hotkey

> Noise is the enemy. Capturing everything makes retrieval worthless.

---


### What you explicitly do NOT capture (noise control)

Block the following(harder than capturing):

- Social media feeds
- Email inboxes
- Shopping pages
- Pages under 200 words
- Pages visited under 15 seconds
- Duplicate URLs within 7 days

---

## 2. Processing Pipeline

All steps run async in the background via Celery. The ingestion endpoint returns immediately with a job ID.

---

### Step 1 — Ingest & Clean

Raw HTML → `Readability.js` (browser) or `trafilatura` (server) → clean text.

Strip boilerplate, navigation, ads. Extract structured metadata:
- Title
- Author
- Publish date
- Domain
- Word count

---

### Step 2 — Chunk Strategy

Use **parent-child chunking**:

- Large parent chunks: **1024 tokens** — for context
- Small child chunks: **256 tokens** — for precise retrieval
- Store both, link child → parent

For long documents, use **semantic chunking** — spliting on topic boundaries, not character count.

---

### Step 3 — Embed

Embed child chunks.

Store vectors in Qdrant with payload:

---

### Step 4 — Entity Extraction → Knowledge Graph

Use Claude or spaCy to extract named entities and relationships from each document. Write them as nodes and edges to Neo4j.

**TMaking it a "knowledge OS" vs a plain vector store.**


---

### Step 5 — Deduplication

Use `Hashing` on a content fingerprint before storing. If similarity > 0.92 with an existing document, skip or merge.

Prevents the same article from N different sources polluting retrieval.

---

### Step 6 — Async Task Queue

Steps 2–5 run as Celery tasks. This keeps the Chrome extension feeling snappy — ingestion returns instantly, heavy work happens in background workers.

```
Celery + Redis broker → worker pool → status streamed via SSE
```

---

## 3. Memory Architecture

### 3-tier memory model

| Tier | Store | Read speed | What lives here |
|------|-------|-----------|-----------------|
| Tier 1 — Ephemeral | Python dict (in-process) | ~0ms | Current session context, conversation history with query agent. Cleared on restart. |
| Tier 2 — Session | Redis | ~1ms | Recent ingestion queue, dedup fingerprints, job status, user preferences, search cache (TTL 24h). |
| Tier 3 — Persistent | Qdrant + Neo4j + Postgres | ~5–50ms | Vectors, knowledge graph, document metadata, full text, eval logs. |

---


## 4. Query & Retrieval

### Hybrid retrieval pipeline

---

#### Step 1 — Query Analysis

Classify the query type and route to the appropriate retrieval strategy:

| Query type | Example | Strategy |
|-----------|---------|----------|
| Factual lookup | "What is HyDE?" | BM25 + vector |
| Exploratory | "What do I know about RAG?" | HyDE + vector |
| Entity-centric | "What did I read about Sam Altman?" | Graph traversal first |
| Temporal | "What did I read last week about X?" | Postgres filter + vector |

---

#### Step 2 — Multi-query Expansion (HyDE)

Generate 3 hypothetical answers to the query, embed them, and use as additional search vectors.

Dramatically improves recall for vague or exploratory queries.

```
LlamaIndex: HypotheticalDocumentEmbedder
```

---

#### Step 3 — Parallel Retrieval (vector + graph + BM25)

Run all three simultaneously

Merge results using **Reciprocal Rank Fusion (RRF)**

---

#### Step 4 — Re-ranking

Cross-encoder re-rank top-20 candidates down to top-5.


> This single step cuts hallucination rate significantly.

---

#### Step 5 — Context Assembly & Generation

For each retrieved child chunk, fetch its parent chunk (parent-child retrieval). Assemble context window. Pass to Claude with a citations instruction. Return answer + source URLs.

```
Child chunk (256 tokens) → fetch parent (1024 tokens) → send parent to LLM
```
