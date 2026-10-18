# Enterprise Python Systems Engineering & Architecture (`py_docs`)

A production-grade Python engineering repository and polyglot architecture guide designed for Principal Software Architects and Senior Engineers with 13+ years of experience across **Node.js / TypeScript** and **PHP (Laravel)**.

This repository features **zero placeholders**, strict static typing (`from __future__ import annotations`), complete runnable implementations, automated unit assertions, and canonical official documentation URLs embedded within every module.

---

## 🏛️ Repository Architecture

The workspace is organized into **8 Progressive Enterprise Tiers**, **3 Foundational Computer Science Pillars**, **7 Career Role Alignment Tracks**, and **Specialized Architectural Whitepapers**:

```
py_docs/
├── setup/                             # Environment orchestration, dependencies & health checks
├── level_1_basic/                     # Core Language, Loops, Data Structures & Comprehensions
├── level_2_moderate/                  # Backend HTTP, SQLite transactions & FastAPI forms
├── level_3_high/                      # Async SQLAlchemy 2.0, WebSockets & Concurrency (GIL)
├── level_4_expert/                    # Asyncio Event Loop, Celery + Redis, Clean DDD Architecture
├── level_5_ai_ml_rag_agents/          # Scikit-Learn pipelines, ChromaDB RAG & ReAct Autonomous Agents
├── level_6_cybersecurity_appsec/      # OWASP PBKDF2 hashing, AES-128 Fernet, JWT RBAC & LLM Defense
├── level_7_advanced_ai_systems/       # RAG Triad (Ragas), BM25 Hybrid Search, GraphRAG & vLLM serving
├── level_8_gui_visual_apps/           # CustomTkinter modern UI, Streamlit AI playground & PyQt6 threads
├── dsa/                               # Data Structures & Algorithms (Big-O and C-level memory analysis)
├── advanced_oop/                      # Python Data Model, Protocols, Descriptors, Metaclasses & Patterns
├── data_science_core/                 # NumPy C-strides, SIMD Vectorization, BLAS & Pandas OLAP
└── docs/                              # Deep-dive whitepapers, cheat sheets & career matrices
    ├── career_roles/                  # 7 Role-based syllabi (FSD, AI/ML, MLOps, Data Eng, AppSec)
    ├── official_reference_index.md    # Master documentation index linking every script
    ├── architecture_matrix.md         # Polyglot comparison matrix (Python vs TS vs PHP)
    ├── concurrency_and_gil.md         # In-depth GIL, Asyncio & PEP 703 Free-Threading guide
    ├── dsa_complexity_cheat_sheet.md  # Low-level memory layout & Big-O reference
    ├── polyglot_architecture_comparison_matrix.md # Memory footprints & runtime lifecycles
    ├── ai_ml_interview_playbook.md    # GenAI, RAG, and Vector system design
    └── owasp_llm_security_checklist.md# OWASP LLM01-LLM10 verification gates
```

---

## 🚀 Quick Start & Environment Verification

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.14 AMD64)
- Virtual Environment tool (`venv`)

### 2. Setup Virtual Environment
```bash
# Windows
setup\setup.bat

# Linux / macOS
chmod +x setup/setup.sh && ./setup/setup.sh
```

### 3. Verify Environment
Execute the automated sanity verification script:
```bash
python setup/verify_environment.py
```

---

## 📚 Curriculum & Topic Directory

### Foundational Computer Science Pillars
- **[DSA (Data Structures & Algorithms)](dsa/)**:
  - `01_linked_lists_and_deques.py`: Singly linked list, `collections.deque` block unrolling (66.7x speedup over `list.pop(0)`).
  - `02_stacks_queues_and_heaps.py`: LIFO stack, `PriorityJobQueue` with `heapq`, monotonic tie-breaking, lazy tombstoning.
  - `03_binary_search_trees_bfs_dfs.py`: BST insertion, 3-case deletion with in-order successors, DFS & BFS.
  - `04_graph_algorithms_dijkstra.py`: Directed graph adjacency list, Dijkstra shortest path, Kahn's topological sort.
  - `05_sorting_and_dynamic_programming.py`: In-place Lomuto QuickSort, binary bisect search, 1D space-optimized Knapsack.

- **[Advanced OOP & Metaprogramming](advanced_oop/)**:
  - `01_dunder_magic_methods_data_model.py`: Arithmetic operator overloading, container emulation, hashing contracts.
  - `02_abstract_base_classes_and_protocols.py`: Nominal `abc.ABC` vs structural `typing.Protocol` (PEP 544).
  - `03_descriptors_and_property_decorators.py`: PEP 487 `__set_name__` data descriptors & lazy property caching.
  - `04_metaclasses_and_class_decorators.py`: Dynamic class creation lifecycle, `__init_subclass__` plugin registry.
  - `05_creational_and_behavioral_patterns.py`: Thread-safe Singleton, NotificationFactory, Pub/Sub EventBus.

- **[Data Science Core](data_science_core/)**:
  - `01_numpy_ndarrays_and_vectorization.py`: Contiguous memory strides, transpose views, vectorized Haversine (11.9x speedup).
  - `02_numpy_broadcasting_linear_algebra.py`: Multidimensional broadcasting rules, BLAS Level-3 cosine similarity matrices.
  - `03_pandas_series_and_dataframes.py`: `.loc` vs `.iloc` indexing semantics, median imputation, `np.select` conditional logic.
  - `04_pandas_groupby_aggregations_joins.py`: Multi-metric GroupBy, relational joins (inner/left/outer), pivot tables & crosstabs.
  - `05_pandas_time_series_and_missing_data.py`: DatetimeIndex slicing, frequency resampling, rolling SMA/EMA, and Parquet columnar I/O.

---

### Progressive Enterprise Tiers (Levels 1 – 8)
- **Level 1**: Loops, Dynamic Arrays, Tuples, Dictionaries, Comprehensions, and Generator streams.
- **Level 2**: Synchronous & Async HTTP (`requests`, `httpx`), SQLite parameterized transactions, FastAPI form validation via Pydantic v2.
- **Level 3**: SQLAlchemy 2.0 Async ORM with connection pooling, WebSockets real-time server with heartbeat framing, and Multithreading vs Multiprocessing (GIL analysis).
- **Level 4**: Advanced `asyncio` event loop scheduling, Celery + Redis distributed task queuing with exponential backoff, and Domain-Driven Clean Architecture.
- **Level 5**: Scikit-Learn ML Pipelines, ChromaDB Vector DB with semantic chunking, LangChain LLM orchestration with SSE token streaming, and ReAct autonomous tool-calling agents.
- **Level 6**: OWASP-compliant password hashing (PBKDF2-HMAC-SHA256, 600k iterations), AES-128 Fernet encryption, stateless JWT auth with RBAC dependency injection, and prompt injection defense.
- **Level 7**: Automated RAG Triad evaluation with Ragas, Hybrid Search (Dense embeddings + BM25 via Reciprocal Rank Fusion), Knowledge Graph RAG with NetworkX, vLLM inference serving with PagedAttention, and PEFT LoRA fine-tuning.
- **Level 8**: Desktop GUI engineering with Tkinter reactive state, CustomTkinter modern dark-mode dashboard, Streamlit reactive AI playground, and multithreaded PyQt6 Signals & Slots.

---

## 🔄 Polyglot Architectural Contrast: Python vs Node.js vs PHP

| Dimension | Python 3.14 (CPython) | Node.js (V8) | PHP 8.x (Zend Engine) |
| :--- | :--- | :--- | :--- |
| **Execution Lifecycle** | Long-running daemon (ASGI / WSGI) | Long-running event-driven daemon | Shared-Nothing per-request (FPM) or persistent worker (Octane) |
| **Dynamic Array Memory** | Contiguous pointer vector (`PyListObject`) | `JSArray` with `FixedArray` storage | `zend_array` with 32B `Bucket` structs |
| **Queue Performance** | `collections.deque`: $\mathcal{O}(1)$ chunked unrolled list | `array.shift()`: $\mathcal{O}(N)$ pointer memory move | `SplDoublyLinkedList::shift()`: $\mathcal{O}(1)$ pointer update |
| **Structural Typing** | `typing.Protocol` (PEP 544 duck typing) | TypeScript compile-time `interface` | Nominal `interface` only |
| **Vectorized Compute** | Native SIMD via NumPy (AVX2/AVX-512) | Manual loops over `TypedArray` | Manual loops or PHP-CPP C extensions |
| **Entity Memory Footprint** | ~48B using `@dataclass(slots=True)` | ~64B V8 `JSObject` | ~128B `zend_object` |

For exhaustive architectural and memory layout diagrams, consult:
- [`docs/dsa_complexity_cheat_sheet.md`](docs/dsa_complexity_cheat_sheet.md)
- [`docs/polyglot_architecture_comparison_matrix.md`](docs/polyglot_architecture_comparison_matrix.md)
- [`docs/official_reference_index.md`](docs/official_reference_index.md)

---

## 🎯 Career Role Alignment Tracks

Master roadmaps with syllabus outlines and direct hands-on code mappings:
1. [Master Role Matrix & Transition Strategy](docs/career_roles/00_master_role_matrix.md)
2. [Python Full-Stack Lead / Staff Engineer](docs/career_roles/01_python_full_stack_lead.md)
3. [Applied AI/ML & GenAI Systems Architect](docs/career_roles/02_ai_ml_engineer_architect.md)
4. [MLOps & AI Platform Engineer](docs/career_roles/03_mlops_engineer.md)
5. [Senior Data Scientist / Quantitative Analyst](docs/career_roles/04_data_scientist.md)
6. [Enterprise Data Engineer](docs/career_roles/05_data_engineer.md)
7. [Application Security (AppSec) & DevSecOps Lead](docs/career_roles/06_cybersecurity_appsec.md)

---

## 📜 License & Acknowledgments

Authored for enterprise systems engineers and principal architects. Distributed under the MIT License.
