# GraphOne / FrontierAtlas — AI Intelligence Ingestion Pipeline

A scalable, fault-tolerant, asynchronous data ingestion and enrichment pipeline engineered for the AI and venture ecosystem. It acquires bulk startup, product, and research paper datasets, monitors 24-hour fresh AI news and job signals, normalizes unstructured payloads via a multi-tier LLM fallback engine, and resolves entity names deterministically.

## Architecture Overview

* **Phase I — Massive Bulk Acquisition (`src/scrapers/`)**: Asynchronous `httpx` + `asyncio` scrapers that acquire 1,200+ startups (Y Combinator Directory), 1,200+ AI products (Hugging Face Spaces), and 1,050+ AI research papers (ArXiv API) enriched concurrently with live GitHub repository star counts.
* **Phase II — 24-Hour Fresh Signal Ingestion (`src/scrapers/news.py`, `jobs.py`)**: Monitors 5 AI news feeds and 5 AI job boards with `trafilatura` full-text extraction, `dateparser` relative date normalization, strict 24-hour UTC filtering, and a seen-URL freshness heuristic for dateless pages.
* **Phase III — Multi-Tier LLM Extraction Engine (`src/llm/orchestrator.py`)**: Structured JSON extraction validated via Pydantic v2. Implements a 3-tier fallback chain (`Gemini 2.0 Flash` → `Groq Llama 3.3 70B` → `DeepSeek`), `tiktoken` head+tail truncation to prevent `413 Payload Too Large` errors, and exponential backoff with jitter for `429 Too Many Requests`.
* **Phase IV — Deterministic Entity Resolution (`src/resolver/entity_resolver.py`)**: Strips legal suffixes (`Inc.`, `LLC`, `Labs`, `Corp.`) and maps messy entity strings against a 50-company canonical AI seed list using `rapidfuzz`, logging every transformation to `Entity Mapping Log`.
* **Phase V & VI — Anti-Bot & Production Design (`architecture.pdf`)**: Detailed 3-page system design covering 500,000+ record scaling, tiered anti-bot evasion (`httpx` → `curl_cffi` → `Playwright` stealth), distributed deduplication, and hybrid SQL/Graph/Vector storage.

## Project Structure

```text
graphone-pipeline/
├── src/
│   ├── schemas.py                  # Pydantic v2 canonical schemas
│   ├── export_sheets.py            # Exports all 6 tabs to Excel/Google Sheets
│   ├── run_phase1.py               # Bulk acquisition runner (Startups, Products, Papers)
│   ├── run_phase2.py               # 24-hour fresh News & Jobs runner
│   ├── run_phase4.py               # Entity resolution & mapping log runner
│   ├── scrapers/
│   │   ├── startups.py
│   │   ├── products.py
│   │   ├── papers.py
│   │   ├── news.py
│   │   └── jobs.py
│   ├── llm/
│   │   └── orchestrator.py         # Multi-tier LLM fallback + 413/429 resilience
│   └── resolver/
│       └── entity_resolver.py      # Canonicalization engine + 50-startup seed list
├── architecture.pdf                # 3-page production architecture document
├── requirements.txt
└── README.md