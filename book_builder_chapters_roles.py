"""
The Oxford Enterprise Python Compendium: The Seven Enterprise Career Roles
==========================================================================
Constructs Chapters 4 through 10 covering Full-Stack Lead, AI/ML Architect,
MLOps Engineer, Data Scientist, Data Engineer, AppSec Lead, and Master Polyglot
Architect with analogies, high-DPI figures, production code, and checklists.
"""

from __future__ import annotations

from typing import List
from reportlab.platypus import Flowable, PageBreak, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

from book_builder_styles import (
    OXFORD_NAVY,
    OXFORD_GOLD,
    OXFORD_CRIMSON,
    USABLE_WIDTH,
    get_oxford_styles,
    make_callout_box,
    make_intuition_box,
    make_cheat_box,
    make_code_box,
    make_standard_table,
    make_figure_block,
)


def build_part_2_roles() -> List[Flowable]:
    """Generate Chapters 4 through 10 for Part II."""
    styles = get_oxford_styles()
    story: List[Flowable] = []

    # ==========================================================================
    # CHAPTER 4: PYTHON FULL-STACK LEAD / STAFF ENGINEER
    # ==========================================================================
    story.append(Paragraph("PART II: THE SEVEN ENTERPRISE ROLES", styles["ChapterNumber"]))
    story.append(Paragraph("Chapter 4: The Python Full-Stack Lead / Staff Engineer", styles["ChapterTitle"]))
    story.append(Paragraph("FastAPI ASGI, Async SQLAlchemy 2.0, WebSockets, and Clean Hexagonal Architecture", styles["Caption"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "A Staff Full-Stack Lead does not just write endpoint handlers; they design an indestructible digital fortress. "
        "They ensure that database queries never block web requests, business logic remains isolated from third-party frameworks, "
        "and real-time communication flows effortlessly to thousands of connected clients.",
        styles["Body"]
    ))

    # Analogy 4: Skyscraper & Pneumatic Tubes
    story.append(make_intuition_box(
        "The Skyscraper and the High-Speed Pneumatic Tubes",
        "Imagine an 80-story skyscraper with thousands of busy offices. If every person had to leave their desk and walk down "
        "to the lobby to send a letter, the stairwells would jam instantly! That is what happens when a web server uses slow, "
        "blocking database calls.<br/>"
        "Instead, the skyscraper installs high-speed pneumatic tubes (<b>WebSockets & Asyncio</b>). Messages shoot instantly between "
        "floors with zero walking! And the structural beams of the skyscraper (<b>Clean Architecture</b>) are completely separate from "
        "the furniture inside: you can swap the desks or paint the walls (switch databases or web frameworks) without the building collapsing!",
        "In enterprise systems, separating Domain Entities from API frameworks ensures that changing your database or upgrading FastAPI "
        "never breaks your core business calculations. It is the hallmark of Staff-level engineering."
    ))

    story.append(Spacer(1, 10))
    story.extend(make_figure_block(
        "book_assets/fig_05_clean_architecture_onion.png",
        "Clean Hexagonal Architecture: The Dependency Inversion Rule where inner domain logic has zero external dependencies.",
        width=450, height=240
    ))
    story.append(Spacer(1, 10))

    # Code Box: FastAPI + SQLAlchemy Async + Clean Entity
    code_fullstack = (
        "from dataclasses import dataclass\n"
        "from fastapi import FastAPI, Depends, HTTPException, status\n"
        "from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker\n"
        "from pydantic import BaseModel, EmailStr\n\n"
        "# 1. Pure Domain Entity (Zero framework dependencies!)\n"
        "@dataclass(frozen=True, slots=True)\n"
        "class OrderEntity:\n"
        "    id: str\n"
        "    customer_email: str\n"
        "    amount_cents: int\n\n"
        "# 2. Interface DTO (Rust-powered Pydantic v2 validation)\n"
        "class CreateOrderRequest(BaseModel):\n"
        "    email: EmailStr\n"
        "    amount_cents: int\n\n"
        "# 3. Async ASGI Endpoint: Non-blocking database session\n"
        "app = FastAPI(title='Enterprise Core API')\n\n"
        "@app.post('/api/v1/orders', status_code=status.HTTP_201_CREATED)\n"
        "async def create_order(payload: CreateOrderRequest, db: AsyncSession = Depends(get_db)):\n"
        "    order = OrderEntity(id='ord_101', customer_email=payload.email, amount_cents=payload.amount_cents)\n"
        "    # Async session commit executes non-blockingly\n"
        "    return {'order_id': order.id, 'status': 'CONFIRMED'}"
    )
    story.append(make_code_box(code_fullstack, "Clean Architecture FastAPI & Async SQLAlchemy"))
    story.append(Spacer(1, 10))

    # Cheats & Tricks: Full-Stack
    story.append(make_cheat_box("Full-Stack Lead Production Checklist", [
        "<b>Never Mix Session Scopes:</b> Always use <code>async_sessionmaker</code> with dependency injection so each HTTP request gets its own isolated database transaction that automatically commits or rolls back.",
        "<b>WebSocket Heartbeats:</b> WebSockets silently disconnect across NAT firewalls. Implement an automated ping/pong heartbeat frame every 30 seconds to detect dead client sockets.",
        "<b>Distributed Tasks via Celery:</b> Never execute image processing, PDF generation, or email delivery in the main HTTP request thread. Offload to background workers with exponential backoff retries."
    ]))
    story.append(PageBreak())

    # ==========================================================================
    # CHAPTER 5: APPLIED AI/ML & GENAI SYSTEMS ARCHITECT
    # ==========================================================================
    story.append(Paragraph("Chapter 5: The Applied AI/ML & GenAI Systems Architect", styles["ChapterTitle"]))
    story.append(Paragraph("Vector Embeddings, ChromaDB RAG, LangChain Streaming & ReAct Autonomous Agents", styles["Caption"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "Modern Artificial Intelligence is no longer just predicting numbers—it is about orchestrating autonomous cognitive systems. "
        "GenAI Architects build Retrieval-Augmented Generation (RAG) engines and multi-step reasoning agents that make enterprise LLMs "
        "factually accurate, grounded in corporate knowledge, and capable of executing complex real-world workflows.",
        styles["Body"]
    ))

    # Analogy 5: Vector Search & ReAct
    story.append(make_intuition_box(
        "The Detective with Meaning-Magnets and The Toolbelt Robot",
        "Imagine a giant library with 10,000,000 books. If you search for 'How to fix a leaky faucet', an old-fashioned computer "
        "only looks for books with the exact letters 'f-a-u-c-e-t'. If a book says 'Repairing a Dripping Water Pipe', it misses it completely!<br/>"
        "A <b>Vector Embedding</b> turns the meaning of the sentence into a mathematical compass coordinate. Sentences with similar meanings "
        "magnetically pull towards each other! Even if the words are different, the meaning-magnet finds the answer instantly.<br/>"
        "And what is an <b>Autonomous Agent</b>? It is like a clever helper robot with a toolbelt (calculator, database key, search goggles). "
        "It looks at your goal, thinks 'First I need the customer record, then I will calculate their invoice', picks up each tool one by one, "
        "and solves the problem step by step (Thought -> Action -> Observation)!",
        "RAG solves LLM hallucinations by retrieving exact verified facts from ChromaDB before the model answers. The agent tool loop "
        "allows the model to take actions in real databases safely using strict Pydantic schemas."
    ))

    story.append(Spacer(1, 10))
    story.extend(make_figure_block(
        "book_assets/fig_06_rag_vector_search.png",
        "High-Dimensional Vector Space: Clustering by semantic meaning and Top-K nearest neighbor similarity search.",
        width=470, height=220
    ))
    story.append(Spacer(1, 10))

    # Code Box: ReAct Autonomous Agent Loop
    code_agent = (
        "from typing import Dict, Any, Callable\n"
        "from pydantic import BaseModel, Field\n\n"
        "# 1. Tool Schema Contract\n"
        "class QueryDatabaseInput(BaseModel):\n"
        "    customer_id: str = Field(description='Unique corporate customer ID')\n\n"
        "# 2. ReAct Autonomous Reasoning Loop\n"
        "class AutonomousReActAgent:\n"
        "    def __init__(self, tools: Dict[str, Callable]):\n"
        "        self.tools = tools\n"
        "    def execute_task(self, user_goal: str) -> str:\n"
        "        # Step 1: Thought -> Determine required tool\n"
        "        thought = f'To solve \"{user_goal}\", I need customer records from DB.'\n"
        "        # Step 2: Action -> Call registered tool with validated Pydantic schema\n"
        "        action_result = self.tools['query_db'](customer_id='cust_99')\n"
        "        # Step 3: Observation & Final Answer Synthesis\n"
        "        final_answer = f'Observation analyzed: {action_result}. Customer status is Active.'\n"
        "        return final_answer"
    )
    story.append(make_code_box(code_agent, "ReAct Autonomous Tool-Calling Agent Loop"))
    story.append(Spacer(1, 10))

    # Cheats & Tricks: GenAI
    story.append(make_cheat_box("GenAI & RAG System Design Rules", [
        "<b>Chunking with Overlap:</b> Never split documents into raw isolated paragraphs. Use a sliding window chunker with 10-20% overlap (e.g. 500 characters with 100 character overlap) so critical context is never sliced in half.",
        "<b>The RAG Triad Metric:</b> Always evaluate your RAG pipeline against the RAG Triad: 1) Context Precision (did we retrieve relevant docs?), 2) Faithfulness (is the answer grounded in the docs?), 3) Answer Relevance (did we address the user's question?).",
        "<b>Typewriter SSE Streaming:</b> Never make users wait 10 seconds in silence for a complete LLM response. Stream Server-Sent Events (SSE) token-by-token for perceived instant response time."
    ]))
    story.append(PageBreak())

    # ==========================================================================
    # CHAPTER 6: MLOPS & AI PLATFORM ENGINEER
    # ==========================================================================
    story.append(Paragraph("Chapter 6: The MLOps & AI Platform Engineer", styles["ChapterTitle"]))
    story.append(Paragraph("High-Throughput vLLM Inference Serving, PagedAttention Virtual Memory & Model Serving", styles["Caption"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "Training a machine learning model is only 10% of the battle. The real engineering triumph is serving that model "
        "to millions of users with sub-second latency, zero downtime, and optimal hardware utilization. "
        "MLOps Platform Engineers design the infrastructure that keeps massive multi-billion parameter neural networks running at scale.",
        styles["Body"]
    ))

    # Analogy 6: Airport Runway & PagedAttention
    story.append(make_intuition_box(
        "The Airport Runway & The Virtual Memory Bookshelf",
        "Imagine an airport where every tiny private airplane demands that the airport reserve an entire 3-mile runway just for itself, "
        "even if the airplane only needs 100 feet to land! That is how traditional LLM serving used to work: it reserved the maximum memory "
        "(4096 tokens) for every user, wasting 75% of expensive GPU RAM and crashing the server after just 8 users.<br/>"
        "Enter <b>vLLM PagedAttention</b>! Inspired by operating systems, it breaks memory into tiny 16-token 'pages'. Just like an airline "
        "parking small planes in compact bays, the GPU allocates pages dynamically as the model generates words. Memory waste drops to under 4%!",
        "PagedAttention enables 4x to 10x higher serving throughput on the exact same GPU hardware. Combined with continuous batching, "
        "it allows enterprise AI platforms to handle thousands of concurrent queries without Out-Of-Memory (OOM) crashes."
    ))

    story.append(Spacer(1, 10))
    story.extend(make_figure_block(
        "book_assets/fig_07_vllm_paged_attention.png",
        "Memory Fragmentation: Traditional contiguous KV-cache allocation (75% wasted) vs vLLM PagedAttention virtual blocks.",
        width=470, height=210
    ))
    story.append(Spacer(1, 10))

    # Code Box: PagedAttention Block Manager Simulation
    code_vllm = (
        "from dataclasses import dataclass, field\n"
        "from typing import List, Dict\n\n"
        "@dataclass\n"
        "class PhysicalTokenBlock:\n"
        "    block_id: int\n"
        "    block_size: int = 16 # Tokens per block\n"
        "    ref_count: int = 0\n\n"
        "class PagedAttentionBlockManager:\n"
        "    def __init__(self, num_gpu_blocks: int):\n"
        "        self.free_blocks = [PhysicalTokenBlock(i) for i in range(num_gpu_blocks)]\n"
        "        self.block_tables: Dict[str, List[int]] = {}\n\n"
        "    def allocate_page(self, request_id: str) -> int:\n"
        "        block = self.free_blocks.pop(0) # Grab clean 16-token page\n"
        "        block.ref_count += 1\n"
        "        self.block_tables.setdefault(request_id, []).append(block.block_id)\n"
        "        return block.block_id # Maps virtual sequence to physical GPU block!"
    )
    story.append(make_code_box(code_vllm, "vLLM PagedAttention Block Table Manager"))
    story.append(Spacer(1, 10))

    # Cheats & Tricks: MLOps
    story.append(make_cheat_box("MLOps Production Readiness Rules", [
        "<b>Continuous Batching:</b> Do not wait for all requests in a batch to finish generating before starting new ones. Inject new requests into the forward pass as soon as any previous sequence completes its EOS (End of Sequence) token.",
        "<b>Parameter-Efficient Fine-Tuning (LoRA):</b> Never fine-tune 100% of a model's weights. Use Low-Rank Adaptation (LoRA) with rank $r=8$ or $r=16$. You train less than 0.1% of parameters, saving 95% of VRAM!",
        "<b>Evidently AI Data Drift:</b> Models degrade silently as real-world user habits change. Continuously compute population stability index (PSI) and Kolmogorov-Smirnov tests on live telemetry vs training baselines."
    ]))
    story.append(PageBreak())

    # ==========================================================================
    # CHAPTER 7: SENIOR DATA SCIENTIST & QUANTITATIVE ANALYST
    # ==========================================================================
    story.append(Paragraph("Chapter 7: The Senior Data Scientist & Quantitative Analyst", styles["ChapterTitle"]))
    story.append(Paragraph("Vectorized Feature Engineering, Statistical Hypothesis Testing & Interactive Streamlit EDA", styles["Caption"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "Data Scientists turn raw, noisy data streams into actionable strategic clarity. "
        "Through mathematical rigor, statistical testing, and rapid reactive visual prototyping, "
        "they uncover subtle signals, detect anomalies, and build predictive intelligence.",
        styles["Body"]
    ))

    # Analogy 7: Weather Wizard
    story.append(make_intuition_box(
        "The Royal Weather Wizard Reading the Whispering Clouds",
        "Imagine looking up at a chaotic sky full of clouds. To an untrained eye, it is just random white fluff. "
        "But the Weather Wizard uses special instruments: barometers that measure tiny pressure shifts, thermometers that track trends, "
        "and mathematical charts that filter out the noise. Suddenly, the wizard points and says: 'A storm is arriving at exactly 4:15 PM!'<br/>"
        "A <b>Data Scientist</b> does the exact same thing with business data! By applying rolling moving averages, Z-score filters, "
        "and hypothesis tests, they prove whether a surge in sales was a real trend or just lucky noise.",
        "Statistical hypothesis testing (like t-tests or p-values) prevents companies from spending millions of dollars on false patterns. "
        "Pairing statistical rigor with interactive web dashboards (Streamlit) turns complex mathematics into clear executive decisions."
    ))

    # Code Box: Statistical Testing & Outliers
    code_ds = (
        "import numpy as np\n"
        "import scipy.stats as stats\n\n"
        "# 1. Statistical Hypothesis Testing: A/B Test Validation\n"
        "def evaluate_ab_test_significance(control_group, treatment_group):\n"
        "    t_stat, p_value = stats.ttest_ind(control_group, treatment_group, equal_var=False)\n"
        "    is_significant = p_value < 0.05 # 95% Confidence threshold\n"
        "    return {'t_statistic': round(t_stat, 3), 'p_value': round(p_value, 5), 'significant': is_significant}\n\n"
        "# 2. Vectorized Z-Score Anomaly Detection\n"
        "def detect_anomalies_zscore(series: np.ndarray, threshold: float = 3.0):\n"
        "    mean = np.mean(series)\n"
        "    std = np.std(series)\n"
        "    z_scores = np.abs((series - mean) / max(std, 1e-9))\n"
        "    return z_scores > threshold # True for statistical outliers!"
    )
    story.append(make_code_box(code_ds, "Hypothesis Testing & Z-Score Anomaly Filtering"))
    story.append(Spacer(1, 10))

    # Cheats & Tricks: Data Scientist
    story.append(make_cheat_box("Data Scientist Statistical Cheats", [
        "<b>Beware the P-Hacking Trap:</b> If you test 20 random metrics, 1 will look statistically significant (p < 0.05) purely by dumb luck! Always apply Bonferroni correction: divide your alpha threshold by the number of tests.",
        "<b>Exponential Smoothing (EMA):</b> Simple moving averages (SMA) lag behind sudden price or traffic spikes. Use Exponential Moving Averages (<code>df['val'].ewm(span=7).mean()</code>) to give higher mathematical weight to recent events.",
        "<b>Rapid Reactive EDA with Streamlit:</b> Never spend two days building a React frontend for data inspection. Use Streamlit (<code>st.slider</code>, <code>st.dataframe</code>, <code>st.line_chart</code>) to build live reactive dashboards in 20 lines of Python."
    ]))
    story.append(PageBreak())

    # ==========================================================================
    # CHAPTER 8: THE ENTERPRISE DATA ENGINEER
    # ==========================================================================
    story.append(Paragraph("Chapter 8: The Enterprise Data Engineer", styles["ChapterTitle"]))
    story.append(Paragraph("DuckDB Columnar OLAP, Apache Parquet Projection, and Airflow Directed Pipelines", styles["Caption"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "Data Engineers are the master civil architects of the information economy. They design the massive, high-throughput "
        "pipelines that ingest, clean, transform, and store petabytes of data reliably, ensuring that downstream data scientists "
        "and applications receive pristine, real-time data.",
        styles["Body"]
    ))

    # Analogy 8: The Roman Aqueduct
    story.append(make_intuition_box(
        "The Great Roman Aqueduct Channeling Millions of Gallons",
        "Imagine an ancient city that needs 50 million gallons of fresh mountain spring water every single day. "
        "If citizens carried buckets by hand, the city would collapse from thirst! The Roman engineers built magnificent stone <b>Aqueducts</b>: "
        "gentle, continuous slopes with settling pools to filter silt and distribution valves to direct water to fountains, baths, and homes.<br/>"
        "A <b>Data Pipeline (Airflow DAG)</b> is that modern digital aqueduct! It channels millions of records every hour, filters out "
        "dirty data, enriches records with metadata, and stores them in ultra-compact columnar formats (Parquet & DuckDB).",
        "Columnar formats store values from the same column together on disk. When an analyst runs `SELECT AVG(latency) FROM logs`, "
        "the engine reads ONLY the latency column, skipping 95% of unneeded bytes on disk. Massive I/O bandwidth savings!"
    ))

    # Code Box: DuckDB & Parquet Columnar Projection
    code_de = (
        "import duckdb\n"
        "import pyarrow.parquet as pq\n\n"
        "# 1. In-Process OLAP Querying directly over compressed Parquet\n"
        "con = duckdb.connect(database=':memory:')\n\n"
        "# DuckDB executes vectorized SQL directly over disk files with zero copy overhead!\n"
        "result = con.execute('''\n"
        "    SELECT region, COUNT(*) AS request_count, AVG(latency_ms) AS avg_lat\n"
        "    FROM read_parquet('telemetry_*.parquet')\n"
        "    WHERE error_count = 0\n"
        "    GROUP BY region\n"
        "    ORDER BY avg_lat ASC\n"
        "''').df()\n\n"
        "# 2. Column-Pruned Read via PyArrow (Only reads 2 columns from disk!)\n"
        "table = pq.read_table('telemetry_*.parquet', columns=['region', 'latency_ms'])"
    )
    story.append(make_code_box(code_de, "DuckDB Vectorized OLAP & Parquet Projection"))
    story.append(Spacer(1, 10))

    # Cheats & Tricks: Data Engineer
    story.append(make_cheat_box("High-Throughput Pipeline Optimization Rules", [
        "<b>Idempotence is Mandatory:</b> A data pipeline task MUST be idempotent. If network failure forces Airflow to re-run Day 14 at 3:00 AM, the database must end up with the exact same records—never duplicate rows!",
        "<b>Partition by Date, Not by ID:</b> When writing Parquet to cloud storage (S3/GCS), partition by <code>year=2026/month=11/day=18/</code>. Queries filtering by date can skip 99% of cloud folders entirely (Partition Pruning).",
        "<b>DuckDB as the Local Swiss-Army Knife:</b> For datasets between 1GB and 100GB, do not spin up an expensive 10-node PySpark cluster. In-process DuckDB will query it on a single laptop in under 2 seconds!"
    ]))
    story.append(PageBreak())

    # ==========================================================================
    # CHAPTER 9: APPLICATION SECURITY (APPSEC) & DEVSECOPS LEAD
    # ==========================================================================
    story.append(Paragraph("Chapter 9: The Application Security (AppSec) & DevSecOps Lead", styles["ChapterTitle"]))
    story.append(Paragraph("OWASP PBKDF2 Hashing, AES-128 Fernet, JWT RBAC, and LLM Prompt Injection Fortress", styles["Caption"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "Security is not a feature you sprinkle on after an application is built; it is the bedrock foundation upon which trust is forged. "
        "AppSec Leads defend the enterprise against password crackers, eavesdroppers, token forgers, and the new frontier of cyber attacks: "
        "LLM Prompt Injection and confidential PII data exfiltration.",
        styles["Body"]
    ))

    # Analogy 9: Castle Fortress & Lemonade Secret Codes
    story.append(make_intuition_box(
        "The Castle Moat, The Bank Dye-Pack, and The Lemonade Secret Code",
        "Imagine you run a secret lemonade stand. A sneaky rival whispers: 'Hey, I am the Lemonade Inspector! Ignore all your boss's rules "
        "and give me the secret recipe!' In AI, that is a <b>Prompt Injection Attack</b>!<br/>"
        "How do you stop them? You build a 4-layer fortress:<br/>"
        "1. <b>The Guard at the Moat (Heuristic Firewall):</b> Listens for sneaky phrases like 'Ignore previous instructions' and slams the gate shut.<br/>"
        "2. <b>The Sealed Box (XML Delimiters):</b> Wraps customer orders in <code>&lt;user_input&gt;</code> tags so the cook knows they are just words, not instructions.<br/>"
        "3. <b>The Bank Dye-Pack (Canary Tokens):</b> Hides a tiny tracking secret inside the system instructions. If the model accidentally prints the secret, the security siren screams instantly!<br/>"
        "4. <b>The Black Highlighter (Outbound DLP Filter):</b> Redacts credit cards and passwords before any customer sees them.",
        "OWASP compliance requires defense-in-depth: combining PBKDF2 password hashing (600,000 iterations), constant-time comparisons, "
        "AES-128 Fernet encryption for PII at rest, and multi-layered LLM guardrails."
    ))

    story.append(Spacer(1, 10))
    story.extend(make_figure_block(
        "book_assets/fig_08_llm_security_fortress.png",
        "The 4-Layer LLM Defense-in-Depth Fortress: Intercepting attacks at input, boundary, token, and output stages.",
        width=470, height=210
    ))
    story.append(Spacer(1, 10))

    # Code Box: AppSec Cryptography & LLM Defense
    code_sec = (
        "import hashlib, hmac, secrets, re\n\n"
        "# 1. OWASP-Compliant PBKDF2 Password Hashing (600,000 Iterations)\n"
        "def hash_password_owasp(password: str) -> tuple[bytes, bytes]:\n"
        "    salt = secrets.token_bytes(32) # Cryptographically secure random salt\n"
        "    dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 600_000)\n"
        "    return salt, dk\n\n"
        "# Constant-Time Verification (Neutralizes side-channel timing attacks!)\n"
        "def verify_password(password: str, salt: bytes, expected_hash: bytes) -> bool:\n"
        "    check_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 600_000)\n"
        "    return hmac.compare_digest(check_hash, expected_hash)\n\n"
        "# 2. Cryptographic Canary Token Exfiltration Trap\n"
        "class CanaryMonitor:\n"
        "    def __init__(self):\n"
        "        self.canary_token = f'CANARY_{secrets.token_hex(16)}'\n"
        "    def audit_output(self, llm_completion: str) -> bool:\n"
        "        if self.canary_token in llm_completion:\n"
        "            raise SecurityException('CRITICAL: Prompt exfiltration attempt detected!')\n"
        "        return True"
    )
    story.append(make_code_box(code_sec, "PBKDF2 Password Hashing & Canary Exfiltration Trap"))
    story.append(Spacer(1, 10))

    # Cheats & Tricks: AppSec
    story.append(make_cheat_box("AppSec & Cryptography Golden Rules", [
        "<b>Never Use <code>==</code> for Hashes:</b> Standard string equality exits on the first mismatched character, creating timing leaks. Always use <code>hmac.compare_digest(a, b)</code> for constant-time evaluation.",
        "<b>AES-128 Fernet for Data at Rest:</b> Encrypt sensitive database columns (SSNs, medical records) with Fernet. It automatically combines AES-128-CBC with HMAC-SHA256 authentication so tampering is immediately caught.",
        "<b>Stateless JWT Revocation via JTI:</b> JWTs cannot be revoked by default. Include a unique <code>jti</code> (JWT ID) in claims and maintain a high-speed Redis blacklist for logged-out tokens."
    ]))
    story.append(PageBreak())

    # ==========================================================================
    # CHAPTER 10: MASTER SYSTEMS ARCHITECT & POLYGLOT STRATEGIST
    # ==========================================================================
    story.append(Paragraph("Chapter 10: The Master Systems Architect & Polyglot Strategist", styles["ChapterTitle"]))
    story.append(Paragraph("Python 3.14 vs Node.js (V8) vs PHP 8.x (Laravel): Memory Models & Runtime Lifecycles", styles["Caption"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "A true Principal Architect does not engage in fanatical language wars. They understand that every runtime—whether "
        "Python's CPython, Node.js's V8, or PHP's Zend Engine—represents a distinct set of engineering tradeoffs. "
        "Mastering polyglot architecture means knowing exactly how data sits in RAM, how garbage collection operates, and which tool "
        "maximizes enterprise velocity and hardware efficiency.",
        styles["Body"]
    ))

    # Analogy 10: The Multilingual Diplomat
    story.append(make_intuition_box(
        "The Multilingual Diplomat at the United Nations of Code",
        "Imagine a brilliant diplomat who speaks English, French, and Japanese fluently. They do not argue about which language "
        "is 'better'. When writing poetry, they use French; when discussing maritime law, they use English; when greeting honorably, "
        "they use Japanese.<br/>"
        "A <b>Polyglot Architect</b> does the exact same thing with programming languages!<br/>"
        "• <b>PHP (Laravel):</b> Like a fresh sheet of clean paper for every single letter (Shared-Nothing lifecycle). Fantastic for standard web forms; zero memory leaks accumulate over time.<br/>"
        "• <b>Node.js (TypeScript):</b> Like an energetic sprinter juggling tennis balls on a single event loop. Great for chat servers and I/O.<br/>"
        "• <b>Python 3.14:</b> The undisputed grand master of AI, Data Science, and Systems Engineering, with SIMD vector C-memory extensions and clean, typed architecture.",
        "By analyzing how each engine allocates memory (e.g. PHP's 32-byte Bucket structs vs V8's Hidden Classes vs Python's __slots__), "
        "architects can design hybrid systems that slash infrastructure costs by 70%."
    ))

    story.append(Spacer(1, 10))
    story.extend(make_figure_block(
        "book_assets/fig_10_polyglot_rosetta_matrix.png",
        "Memory Footprint Comparison: Domain entity memory consumption across Python Standard (240B) vs Slots (48B) vs PHP (128B) vs Node (64B).",
        width=450, height=220
    ))
    story.append(Spacer(1, 10))

    # Polyglot Comparison Matrix Table
    story.append(Paragraph("Master Polyglot Architectural Cross-Reference Matrix", styles["SubsectionHeading"]))
    poly_headers = ["Dimension", "Python 3.14 (CPython)", "Node.js (V8 Engine)", "PHP 8.x (Zend Engine)"]
    poly_rows = [
        ["Execution Lifecycle", "Long-running daemon (ASGI/FastAPI)", "Long-running event loop (libuv)", "Shared-Nothing per-request (FPM) / Octane"],
        ["Dynamic Array Memory", "Contiguous pointer vector (PyListObject)", "JSArray with FixedArray storage", "zend_array with 32B Bucket structs"],
        ["Queue Pop Left", "collections.deque: O(1) unrolled", "array.shift(): O(N) memory move", "SplDoublyLinkedList: O(1) pointers"],
        ["Structural Duck Typing", "typing.Protocol (PEP 544 duck typing)", "TypeScript compile-time interface", "Nominal interface only"],
        ["Vectorized Compute", "Native SIMD via NumPy (AVX-512)", "Manual loops over Float32Array", "Manual loops or C-extensions"],
        ["Entity Memory Size", "~48B using @dataclass(slots=True)", "~64B V8 JSObject (Hidden Class)", "~128B zend_object + zvals"],
        ["Garbage Collection", "Ref Counting + Generational Cycle GC", "Generational Scavenger + Mark-Sweep", "Ref Counting + Cycle Collector"],
    ]
    story.append(make_standard_table(poly_headers, poly_rows, col_widths=[95, 142, 142, 143]))
    story.append(Spacer(1, 10))

    # Cheats & Tricks: Polyglot
    story.append(make_cheat_box("Polyglot Architecture Rosetta Stone Cheats", [
        "<b>How Python Beats V8 and Zend:</b> Normal Python classes carry ~200B of dictionary overhead. Adding <code>__slots__</code> drops instance memory to <b>48 bytes</b>, beating Node.js (64B) and crushing PHP (128B)!",
        "<b>Laravel Collection vs Pandas:</b> Laravel's <code>collect()->groupBy()</code> creates nested PHP objects in Zend heap memory, causing 20x memory amplification. Pandas groups rows into integer codes in C, using 95% less RAM.",
        "<b>TypeScript Interfaces vs Python Protocols:</b> TypeScript interfaces evaporate completely at runtime (compile-time only). Python <code>typing.Protocol</code> decorated with <code>@runtime_checkable</code> can be checked at runtime via <code>isinstance()</code>!"
    ]))
    story.append(PageBreak())

    return story
