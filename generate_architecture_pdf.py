from fpdf import FPDF


class ArchitecturePDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(120, 120, 120)
            self.cell(0, 8, "GraphOne / FrontierAtlas - Production Data Intelligence Architecture", align="R")
            self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Page {self.page_no()} of 3", align="C")

    def section_title(self, title: str):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(20, 45, 90)
        self.cell(0, 9, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(20, 45, 90)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)

    def sub_title(self, title: str):
        self.set_font("Helvetica", "B", 10.5)
        self.set_text_color(40, 40, 40)
        self.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")

    def body_text(self, text: str):
        self.set_font("Helvetica", "", 9.5)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 5.2, text)
        self.ln(2)

    def bullet(self, lead: str, text: str):
        self.set_font("Helvetica", "B", 9.5)
        self.set_text_color(30, 30, 30)
        self.cell(5, 5.2, "-")
        self.write(5.2, f"{lead}: ")
        self.set_font("Helvetica", "", 9.5)
        self.write(5.2, text)
        self.ln(6)


def build_pdf():
    pdf = ArchitecturePDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # ================= PAGE 1 =================
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(15, 35, 75)
    pdf.cell(0, 10, "GraphOne / FrontierAtlas", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 7, "Production Technical Architecture: Scalable AI Intelligence Graph Pipeline", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    pdf.section_title("1. Scale Strategy: Collecting 500,000+ Records Without Manual Intervention")
    pdf.body_text(
        "Scaling from 3,000 trial records to 500,000+ startups, products, and research papers requires decoupling "
        "URL discovery from content extraction and LLM normalization using an event-driven producer-consumer architecture."
    )
    pdf.bullet(
        "Distributed URL Frontier (Apache Kafka / Redis Streams)",
        "Seeders push paginated directory URLs, sitemaps, and API cursors into partitioned Kafka topics (startups.raw, products.raw, papers.raw). Partitioning by domain prevents overwhelming any single target host."
    )
    pdf.bullet(
        "Stateless Autoscaled Worker Pools (Kubernetes + KEDA)",
        "Async Python workers (asyncio + httpx) consume from Kafka. KEDA autoscales worker pods from 5 to 200+ based on Kafka consumer lag, enabling linear throughput scaling without code changes."
    )
    pdf.bullet(
        "Checkpointing & Dead-Letter Queues (DLQ)",
        "Every raw HTML/JSON payload is persisted immediately to object storage (S3/GCS) as immutable Parquet/JSONL files. Failed URLs after max retries route to a DLQ for automated replay or escalation to headless browsers."
    )
    pdf.bullet(
        "GitHub Metric Enrichment at Scale",
        "To track dynamic stars across 100k+ repositories without hitting the 5,000 req/hr REST limit, workers batch up to 100 repos per query using the GitHub GraphQL API across a rotated pool of GitHub App installation tokens."
    )

    pdf.ln(2)
    pdf.section_title("2. Anti-Bot Navigation & Tiered Fetcher Strategy")
    pdf.body_text(
        "High-value venture directories and job boards frequently deploy Cloudflare, Datadome, or heavy client-side JS. "
        "Rather than running expensive headless browsers on every URL, the pipeline uses a cost-optimized 3-tier escalation fetcher:"
    )
    pdf.bullet(
        "Tier 1 - Fast Async HTTP (httpx)",
        "Handles ~75% of traffic (public APIs, RSS feeds, static HTML) with HTTP/2 connection pooling and minimal CPU/RAM overhead."
    )
    pdf.bullet(
        "Tier 2 - TLS Fingerprint Impersonation (curl_cffi)",
        "Triggered automatically on HTTP 403/429 or Cloudflare JS challenge headers. Impersonates real Chrome/Safari JA3/JA4 TLS fingerprints and HTTP/2 frames to bypass standard WAFs without browser overhead."
    )
    pdf.bullet(
        "Tier 3 - Stealth Headless Browser (Playwright Async + Residential Proxies)",
        "Reserved for aggressive Datadome/SPA targets. Uses Playwright with stealth patches, randomized viewport/timezone fingerprints, and sticky residential proxy sessions."
    )

    # ================= PAGE 2 =================
    pdf.add_page()
    pdf.section_title("3. Handling 413s & 429s Across Thousands of Concurrent Extractions")
    pdf.body_text(
        "LLM APIs introduce two primary production failure modes: context window overflows (413 Payload Too Large) "
        "and provider rate limits (429 Too Many Requests). The LLMOrchestrator isolates these failures deterministically."
    )

    pdf.sub_title("Preventing 413 Payload Too Large (Semantic Pruning + Token Budgeting)")
    pdf.bullet(
        "DOM Boilerplate Stripping",
        "Before tokenization, raw HTML is passed through Trafilatura / BeautifulSoup to strip scripts, CSS, navbars, and footers. This reduces payload size by 70-85% while increasing signal density."
    )
    pdf.bullet(
        "Deterministic Head + Tail Truncation",
        "Using tiktoken (cl100k_base), payloads exceeding the 3,500-token budget are truncated to retain the top 75% (titles, metadata, opening paragraphs) and bottom 25% (publication dates, author bios, pricing footers)."
    )
    pdf.bullet(
        "Map-Reduce Chunking for Long Documents",
        "For full research papers or SEC filings where truncation loses facts, documents are split into overlapping 3,000-token chunks, extracted in parallel, and merged via a deterministic schema reducer."
    )

    pdf.sub_title("Surviving 429 Rate Limits (Multi-Tier Fallback + Distributed Token Buckets)")
    pdf.bullet(
        "Global Redis Token Bucket",
        "Across hundreds of worker pods, a shared Redis Lua script enforces per-provider RPM (requests/min) and TPM (tokens/min) ceilings proactively, preventing thundering-herd 429 storms."
    )
    pdf.bullet(
        "Exponential Backoff with Jitter",
        "On transient 429s, workers back off using delay = (2 ** attempt) + uniform(0.2, 1.0) seconds, respecting Retry-After headers when present."
    )
    pdf.bullet(
        "3-Tier Provider Fallback Chain",
        "If Tier 1 (Gemini 2.0 Flash) exhausts quota or returns 5xx/429s, the orchestrator seamlessly routes the exact Pydantic schema prompt to Tier 2 (Groq Llama 3.3 70B) and Tier 3 (DeepSeek), logging every transition for cost/latency monitoring."
    )

    pdf.ln(2)
    pdf.section_title("4. Freshness Tracking & Distributed Deduplication")
    pdf.body_text(
        "Guaranteeing 24-hour freshness for AI news and jobs while ensuring distributed crawler nodes never process "
        "the same item twice requires multi-layer deduplication and date normalization."
    )
    pdf.bullet(
        "URL Canonicalization & Redis Bloom Filter",
        "Before fetching, URLs are stripped of tracking parameters (utm_*, ref) and hashed (SHA-256). A distributed Redis Bloom Filter / Set with a 30-day TTL provides O(1) atomic checks across all crawler nodes."
    )
    pdf.bullet(
        "Near-Duplicate Detection (SimHash / MinHash)",
        "Syndicated news articles often appear on multiple domains with different URLs. Computing a 64-bit SimHash on extracted text catches >95% similar articles and suppresses duplicate LLM calls."
    )
    pdf.bullet(
        "Date Normalization & Missing-Date Heuristics",
        "Timestamps are parsed via dateparser into strict UTC ISO-8601. If a page lacks a publication date, the system checks its first_seen_at timestamp in Redis/Postgres; only items unseen in prior crawl cycles are admitted as fresh."
    )

    # ================= PAGE 3 =================
    pdf.add_page()
    pdf.section_title("5. Storage Strategy: Hybrid Relational, Graph, and Vector Architecture")
    pdf.body_text(
        "An Intelligence Graph spanning startups, founders, products, papers, jobs, and news has three distinct access "
        "patterns: transactional ACID writes, multi-hop relationship traversal, and semantic similarity search. "
        "A single database cannot optimize all three cleanly; therefore, we use a polyglot storage architecture."
    )

    pdf.bullet(
        "Primary System of Record - PostgreSQL (with JSONB & TimescaleDB)",
        "Stores all canonical entities (Startups, Products, Papers, Jobs, News) with strict schema enforcement, unique constraints on source URLs, and JSONB columns for raw flexible metadata. TimescaleDB hypertables partition time-series metrics (daily GitHub star deltas, job posting velocity) for fast trend queries."
    )
    pdf.bullet(
        "Intelligence Graph Layer - Neo4j (Synced via CDC / Debezium)",
        "Maps complex multi-hop relationships: (Founder)-[:FOUNDED]->(Startup)-[:BUILT]->(Product), (Author)-[:WROTE]->(Paper)-[:HAS_CODE]->(GitHubRepo). Enables instant graph queries (e.g., 'Find all startups founded by authors of top-1000-star ArXiv papers') that would require prohibitively slow SQL JOINs."
    )
    pdf.bullet(
        "Vector & Semantic Entity Resolution - Qdrant / pgvector",
        "Stores dense text embeddings of startup descriptions, product names, and news articles. Powers semantic search and Stage-2 entity resolution when deterministic string/fuzzy matching (RapidFuzz) falls into an ambiguous 75-87% confidence band."
    )
    pdf.bullet(
        "Raw Data Lake - Amazon S3 / Google Cloud Storage (Parquet)",
        "Retains immutable raw HTML/API snapshots and LLM extraction audit logs. Enables full pipeline replay whenever canonical schemas upgrade (e.g., schemaVersion 1.0 -> 2.0) without re-scraping external websites."
    )

    pdf.ln(3)
    pdf.section_title("6. Production Observability & Data Fidelity Guardrails")
    pdf.bullet(
        "Zero-Hallucination Lineage Enforcement",
        "Every record persisted to PostgreSQL must pass Pydantic validation with a non-empty, HTTP-200 verified source.url and ISO-8601 collectedAt timestamp. Any LLM output failing schema or URL lineage checks is quarantined."
    )
    pdf.bullet(
        "Real-Time Telemetry (Prometheus + Grafana)",
        "Tracks per-domain HTTP status codes (200 vs 403/429), LLM fallback rates, token spend per 1,000 records, and 24-hour freshness lag so engineers are alerted immediately if a target site changes its DOM layout."
    )

    pdf.output("architecture.pdf")
    print("Successfully generated 3-page architecture.pdf!")


if __name__ == "__main__":
    build_pdf()