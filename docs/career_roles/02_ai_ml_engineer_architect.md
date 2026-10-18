<!--
Applied AI/ML & Generative AI Architect Syllabus
================================================
Description: Comprehensive enterprise syllabus for Applied AI/ML Engineers and Generative AI
             Solutions Architects. Covers Scikit-Learn pipelines, ChromaDB vector databases,
             ReAct tool calling, GraphRAG, vLLM serving, LoRA fine-tuning, and MCP protocols.
Enterprise Mapping: Translates frontend/backend AI integrations (LangChain.js, Vercel AI SDK)
                    into native Python high-throughput deep learning and retrieval architectures.

Official Documentation References:
- Scikit-Learn Pipeline Guide: https://scikit-learn.org/stable/modules/compose.html
- ChromaDB Vector Store: https://docs.trychroma.com/
- LangChain Official Documentation: https://python.langchain.com/docs/introduction/
- NetworkX Network Analysis: https://networkx.org/
- vLLM High-Throughput Engine: https://docs.vllm.ai/
- Hugging Face PEFT LoRA: https://huggingface.co/docs/peft/
- Anthropic Model Context Protocol (MCP): https://modelcontextprotocol.io/
- Ragas RAG Evaluation Framework: https://docs.ragas.io/
-->

# Applied AI/ML & Generative AI Architect

## 1. Role Overview & Strategic Positioning

The **Applied AI/ML & Generative AI Architect** designs, deploys, and scales machine learning pipelines, vector retrieval-augmented generation (RAG) platforms, autonomous tool-calling agents, and fine-tuned LLM serving backbones. This role ensures that generative models operate with low latency, high faithfulness, deterministic structured outputs, and enterprise cost-efficiency.

### Enterprise Ecosystem Translation

| AI / ML Engineering Domain | TypeScript / JavaScript Ecosystem | Python Production Standard (Canonical) |
|---|---|---|
| **Classical ML / Feature Prep** | TensorFlow.js, Brain.js | **NumPy, SciPy, Scikit-Learn, Pandas** |
| **Model Serialization** | JSON, ONNX Web Runtime | **Joblib, Safetensors, Pickle (internal only)** |
| **Vector Database Clients** | Pinecone TS SDK, Weaviate-ts | **ChromaDB, Qdrant, Milvus, pgvector** |
| **LLM Orchestration & Prompts** | LangChain.js, Vercel AI SDK | **LangChain, LlamaIndex, DSPy** |
| **High-Throughput Inference** | External REST APIs (OpenAI/Anthropic) | **vLLM (PagedAttention), TensorRT-LLM, TGI** |
| **Parameter-Efficient Tuning** | N/A (Requires GPU Python toolchains) | **Hugging Face PEFT, LoRA, QLoRA, Axolotl** |
| **Agentic Communication** | Custom JSON function calling | **Model Context Protocol (MCP), ReAct Loop** |
| **RAG Regression Testing** | Manual prompt testing, eval scripts | **Ragas Triad (Faithfulness, Relevance, Precision)** |

---

## 2. Direct Hands-On Evidence Modules (Levels 1–8)

The following modules in this repository provide concrete, production-grade evidence of mastery required for this role:

1. [**`level_5_ai_ml_rag_agents/01_numpy_scikit_ml_pipeline.py`**](file:///P:/prabhu/projects/git_python/py_docs/level_5_ai_ml_rag_agents/01_numpy_scikit_ml_pipeline.py)
   - *Evidence*: High-performance vector math in NumPy (dot products, cosine similarities), Scikit-Learn `Pipeline` (`StandardScaler` + `LogisticRegression`), and binary model artifact serialization with `joblib`.
2. [**`level_5_ai_ml_rag_agents/02_vector_embeddings_chromadb_rag.py`**](file:///P:/prabhu/projects/git_python/py_docs/level_5_ai_ml_rag_agents/02_vector_embeddings_chromadb_rag.py)
   - *Evidence*: Text chunking with sliding window overlap, vector embeddings via `sentence-transformers`, persistent ChromaDB collection storage, and Top-K cosine similarity semantic search.
3. [**`level_5_ai_ml_rag_agents/03_llm_orchestration_langchain.py`**](file:///P:/prabhu/projects/git_python/py_docs/level_5_ai_ml_rag_agents/03_llm_orchestration_langchain.py)
   - *Evidence*: Chat prompt templating, role separation (`system`, `user`, `assistant`), real-time Server-Sent Events (SSE) token streaming, and structured Pydantic v2 output extraction.
4. [**`level_5_ai_ml_rag_agents/04_autonomous_agent_tool_calling.py`**](file:///P:/prabhu/projects/git_python/py_docs/level_5_ai_ml_rag_agents/04_autonomous_agent_tool_calling.py)
   - *Evidence*: ReAct (Reason + Act) autonomous agent loop, custom tool registry with Pydantic argument schemas, and multi-step reasoning across database lookups and API calls.
5. [**`level_7_advanced_ai_systems/01_rag_triad_evaluation_ragas.py`**](file:///P:/prabhu/projects/git_python/py_docs/level_7_advanced_ai_systems/01_rag_triad_evaluation_ragas.py)
   - *Evidence*: Automated RAG Triad hallucination evaluation metrics (Faithfulness, Answer Relevance, Context Precision) using synthetic regression datasets.
6. [**`level_7_advanced_ai_systems/02_hybrid_search_bm25_dense.py`**](file:///P:/prabhu/projects/git_python/py_docs/level_7_advanced_ai_systems/02_hybrid_search_bm25_dense.py)
   - *Evidence*: Reciprocal Rank Fusion (RRF) combining sparse BM25 keyword matching with dense cosine embeddings, overcoming vocabulary mismatch problems.
7. [**`level_7_advanced_ai_systems/03_knowledge_graph_rag.py`**](file:///P:/prabhu/projects/git_python/py_docs/level_7_advanced_ai_systems/03_knowledge_graph_rag.py)
   - *Evidence*: Directed relational knowledge modeling with `networkx`, multi-hop causal lineage traversal, and GraphRAG context synthesis.
8. [**`level_7_advanced_ai_systems/04_vllm_inference_serving.py`**](file:///P:/prabhu/projects/git_python/py_docs/level_7_advanced_ai_systems/04_vllm_inference_serving.py)
   - *Evidence*: High-throughput LLM server architecture utilizing PagedAttention virtual KV-cache memory management, continuous request batching, and prefix caching.
9. [**`level_7_advanced_ai_systems/05_peft_lora_finetuning.py`**](file:///P:/prabhu/projects/git_python/py_docs/level_7_advanced_ai_systems/05_peft_lora_finetuning.py)
   - *Evidence*: Parameter-Efficient Fine-Tuning using Low-Rank Adaptation (LoRA), configuring rank $r$, $\alpha$ scaling, and target projection layers, reducing trainable weights to <0.1%.
10. [**`level_7_advanced_ai_systems/06_semantic_caching_and_router.py`**](file:///P:/prabhu/projects/git_python/py_docs/level_7_advanced_ai_systems/06_semantic_caching_and_router.py)
    - *Evidence*: Vector-based semantic caching (cosine similarity threshold $\ge 0.92$) and dynamic complexity cost routing between lightweight and frontier LLMs.
11. [**`level_8_gui_visual_apps/03_streamlit_reactive_ai_playground.py`**](file:///P:/prabhu/projects/git_python/py_docs/level_8_gui_visual_apps/03_streamlit_reactive_ai_playground.py)
    - *Evidence*: Interactive vector distance inspector and streaming RAG playground for model parameter sensitivity exploration.

---

## 3. Comprehensive Core Syllabus

### Module 1: Classical Machine Learning & Feature Engineering
- **NumPy Vectorization**:
  Replacing slow Python `for` loops with C-accelerated vectorized broadcasting, calculating Euclidean distance matrices and cosine similarities across high-dimensional tensor spaces.
- **Scikit-Learn Pipeline Architecture**:
  Chaining `ColumnTransformer` (scaling numerical features with `StandardScaler` and encoding categorical features with `OneHotEncoder`) directly to estimators (`LogisticRegression`, `RandomForestClassifier`), eliminating data leakage between train and test folds.

### Module 2: Vector Space Engineering & Advanced RAG
- **Chunking Strategies**:
  Recursive character chunking vs Semantic splitting based on embedding distance shifts; sliding window overlap (10–20%) to preserve cross-boundary context.
- **Vector Indexing (HNSW vs IVFFlat)**:
  Hierarchical Navigable Small World (HNSW) graph indexing trade-offs: $M$ (max bidirectional links per node), `efConstruction` (build-time accuracy), and `efSearch` (query-time speed vs recall).
- **Hybrid Search & Reciprocal Rank Fusion (RRF)**:
  Fusing sparse lexical search (BM25 for exact part numbers, acronyms, and names) with dense semantic search (sentence-transformers for conceptual meaning):
  $$\text{RRF Score}(d) = \sum_{m \in M} \frac{1}{k + r_m(d)}$$
  where $k \approx 60$ acts as a smoothing parameter.

### Module 3: Autonomous Agent Engineering & Tool Calling
- **ReAct (Reason + Act) Loop**:
  Structuring LLM outputs into deterministic execution cycles:
  `Thought -> Action -> Action Input -> Observation -> Final Answer`.
- **Pydantic Schema Validation for Function Calling**:
  Using Pydantic v2 to define strict JSON schemas for tools (database lookups, external REST APIs, calculator utilities), preventing hallucinated arguments before invocation.

### Module 4: High-Throughput Serving & Low-Rank Fine-Tuning
- **PagedAttention KV-Cache Management (vLLM)**:
  Eliminating internal GPU memory fragmentation by dividing the Key-Value (KV) cache into non-contiguous virtual memory blocks (analogous to virtual memory paging in operating systems).
- **LoRA (Low-Rank Adaptation)**:
  Freezing pre-trained model weights $W_0 \in \mathbb{R}^{d \times k}$ and injecting trainable rank decomposition matrices $A \in \mathbb{R}^{r \times k}$ and $B \in \mathbb{R}^{d \times r}$ with $r \ll \min(d, k)$:
  $$W = W_0 + \Delta W = W_0 + \frac{\alpha}{r} (B \times A)$$
  Enabling fine-tuning of 70B parameter models on commodity GPUs and merging weights at zero inference latency.

---

## 4. Supplemental Topics (Remaining 20% to 100% Mastery)

### 1. Model Context Protocol (MCP) Standardization
The open standard introduced by Anthropic to standardize how AI agents access enterprise tools, local databases, and external contexts:
- **Architecture**: Separates Host (AI application / IDE), Client (protocol connector), and MCP Servers (isolated service exposing Tools, Resources, and Prompts).
- **Transport Mechanisms**: Standard Input/Output (`stdio`) for local process isolation and Server-Sent Events (`SSE`) for distributed remote microservice agents.
- **Python Implementation**: Building custom MCP servers using the official Python SDK (`mcp` package) with `FastMCP`.
- *Official Docs*: [Model Context Protocol Specification](https://modelcontextprotocol.io/)

### 2. Direct Preference Optimization (DPO) & Alignment
Moving beyond legacy Reinforcement Learning from Human Feedback (RLHF) with complex reward models:
- **DPO Principle**: Directly optimizes the policy model using human preference pairs $(y_w, y_l)$ (chosen vs rejected completions) via binary cross-entropy loss:
  $$\mathcal{L}_{\text{DPO}}(\pi_\theta; \pi_{\text{ref}}) = -\mathbb{E}_{(x, y_w, y_l)} \left[ \log \sigma \left( \beta \log \frac{\pi_\theta(y_w|x)}{\pi_{\text{ref}}(y_w|x)} - \beta \log \frac{\pi_\theta(y_l|x)}{\pi_{\text{ref}}(y_l|x)} \right) \right]$$
- **Hugging Face TRL**: Orchestrating fine-tuning with `DPOTrainer` on curated preference datasets.
- *Official Docs*: [Hugging Face TRL DPO Guide](https://huggingface.co/docs/trl/main/en/dpo_trainer)

### 3. Quantization Mechanics (AWQ, GPTQ, GGUF)
Reducing model memory footprint from FP16 (16 bits) to INT8 or INT4:
- **AWQ (Activation-Aware Weight Quantization)**: Preserving the top 1% salient weights based on activation magnitudes to avoid accuracy degradation.
- **GGUF (GPT-Generated Unified Format)**: Running quantized models on CPU / Apple Silicon unified memory via `llama.cpp`.
- *Official Docs*: [AutoAWQ Documentation](https://casper-hansen.github.io/AutoAWQ/)

### 4. Advanced Multi-Agent Frameworks (LangGraph & CrewAI)
Transitioning from simple linear ReAct loops to cyclical state graphs:
- **LangGraph**: Modeling multi-agent systems as State Graphs with nodes (agents/tools), edges (conditional transitions), and persistent checkpoints for human-in-the-loop approvals.
- *Official Docs*: [LangGraph Guide](https://langchain-ai.github.io/langgraph/)

---

## 5. Curated Documentation & Reference Links

- **Scikit-Learn Machine Learning in Python**: https://scikit-learn.org/stable/
- **ChromaDB Documentation**: https://docs.trychroma.com/
- **Sentence-Transformers (Hugging Face)**: https://sbert.net/
- **LangChain Python Documentation**: https://python.langchain.com/
- **vLLM Inference Serving Engine**: https://docs.vllm.ai/
- **Hugging Face PEFT Library**: https://huggingface.co/docs/peft/
- **Ragas Automated RAG Evaluation**: https://docs.ragas.io/
- **NetworkX Network Analysis**: https://networkx.org/
- **Anthropic Model Context Protocol**: https://modelcontextprotocol.io/
- **Hugging Face TRL (Transformer Reinforcement Learning)**: https://huggingface.co/docs/trl/
