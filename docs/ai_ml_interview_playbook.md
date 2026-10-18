<!--
Enterprise AI/ML & RAG Systems Interview Playbook
=================================================
Description: Architectural system design guide and reference manual covering Vector Search (HNSW),
             Model Quantization, Advanced Chunking Strategies, and RAG Evaluation Frameworks.
Enterprise Mapping: Essential interview and systems architecture reference for Principal Architects
                    transitioning into Staff/Principal AI Platform Engineer roles.

Official Documentation References:
- Hierarchical Navigable Small World (HNSW) Research Paper: https://arxiv.org/abs/1603.09320
- ChromaDB HNSW Indexing Parameters: https://docs.trychroma.com/guides
- Hugging Face Quantization Guide: https://huggingface.co/docs/transformers/main_classes/quantization
- RAG Triad Evaluation (TruLens): https://www.trulens.org/trulens_eval/getting_started/core_concepts/rag_triad/
- Ragas (RAG Assessment) Documentation: https://docs.ragas.io/en/stable/
-->

# Enterprise AI/ML & RAG Systems Architecture Playbook

This technical playbook provides senior architectural answers to foundational system design questions encountered in enterprise AI/ML platform interviews.

---

## 1. Vector Search & Approximate Nearest Neighbor (ANN) Indexing: HNSW Deep Dive

### How Does HNSW (Hierarchical Navigable Small World) Function?
HNSW is the industry standard graph-based ANN indexing algorithm used in ChromaDB, Pinecone, Milvus, and pgvector.

```
Layer 2 (Expressway):  [Doc A] ------------------------------------> [Doc Z]
                             \                                        /
Layer 1 (Sub-highways): [Doc A] ---------> [Doc M] ---------> [Doc T] ---> [Doc Z]
                           |       \          |         \        |           |
Layer 0 (Dense Ground): [Doc A]-[Doc B]-[Doc M]-[Doc P]-[Doc T]-[Doc X]-[Doc Z]
```

1. **Multi-Layer Skip-List Graph Architecture**:
   - High layers contain sparse graphs with long-range edges for high-speed macro-navigation.
   - Lower layers contain dense graphs with short-range edges for fine-grained local neighborhood exploration.
2. **Search Traversal**:
   - The query vector enters at the top layer, performs greedy search to find the local nearest neighbor, drops down to the next layer, and repeats until reaching Layer 0 (the complete dataset).
3. **Core Hyperparameters**:
   - `M` (Max bidirectional connections per node, e.g., 16-64): Higher values increase recall and graph connectivity at the cost of indexing RAM and construction latency.
   - `efConstruction` (Size of dynamic candidate list during graph building, e.g., 100-200): Controls index build quality.
   - `efSearch` (Size of dynamic candidate list during query time, e.g., 50-100): Direct knob tuning the trade-off between search latency and Recall@K.

### Comparison: HNSW vs IVF-PQ (Inverted File with Product Quantization)
| Metric | HNSW | IVF-PQ (e.g., FAISS) |
|---|---|---|
| **Query Latency** | Sub-millisecond (Fastest) | Fast |
| **Recall Rate** | Extremely High (95-99%) | Moderate-High (85-95%) |
| **RAM Footprint** | High (stores vectors + graph edges in memory) | Extremely Low (compressed 8x-16x via codebooks) |
| **Write/Update Cost** | Incremental inserts supported natively | Requires full batch re-clustering |

---

## 2. Model Quantization: Shrinking LLM Footprints

### The Mathematical Core of Quantization
Quantization maps continuous 32-bit floating-point weights (FP32) to lower-bit representations (FP16, INT8, INT4):

$$\text{Quantized Integer} = \text{round}\left(\frac{\text{Weight}}{\text{Scale}}\right) + \text{ZeroPoint}$$

### Memory Footprint Formula
$$\text{VRAM Required (GB)} \approx \frac{\text{Parameters (Billions)} \times \text{Bits Per Weight}}{8} \times 1.25\text{ (KV Cache + Context Overhead)}$$

### Real-World Footprint for a 70B Parameter Model
| Precision | Bits/Weight | Base Model VRAM | Total Serving VRAM (32k context) | Minimum Hardware |
|---|---|---|---|---|
| **FP16 / BF16** | 16 bits (2 bytes) | 140 GB | ~175 GB | 4x NVIDIA A100 (80GB) |
| **INT8 (BitsAndBytes)** | 8 bits (1 byte) | 70 GB | ~88 GB | 2x NVIDIA A100 (80GB) |
| **INT4 (AWQ / GPTQ)** | 4 bits (0.5 byte) | 35 GB | ~44 GB | 1x NVIDIA A100 (80GB) or 2x RTX 4090 (24GB) |

### Modern Quantization Techniques
- **AWQ (Activation-aware Weight Quantization)**: Protects the top 1% salient weights based on activation magnitudes while quantizing remaining weights to 4-bit, retaining ~99% FP16 reasoning benchmarks.
- **GPTQ (One-shot Weight Quantization)**: Second-order Taylor expansion error compensation. High throughput on GPU batch inference.
- **GGUF (llama.cpp)**: CPU-first quantized binary format enabling local execution on commodity Apple Silicon and x86 servers.

---

## 3. Advanced Document Chunking Strategies

```
Raw Text: [ Paragraph 1 ] [ Paragraph 2 ] [ Paragraph 3 ] [ Paragraph 4 ]
               |-----------------|  <-- Chunk 1 (Size: 500, Overlap: 100)
                           |-----------------|  <-- Chunk 2
```

1. **Fixed-Size Chunking with Overlap**:
   - *Mechanism*: Slices text into fixed character or token counts with a 10-20% sliding window.
   - *Trade-off*: Simple to implement; risks breaking mid-sentence or mid-code-block.
2. **Recursive Character Chunking**:
   - *Mechanism*: Hierarchically attempts splitting on `["\n\n", "\n", " ", ""]` to preserve natural paragraph and sentence structure.
3. **Semantic Chunking**:
   - *Mechanism*: Computes consecutive sentence embeddings. When the cosine distance between sentence $N$ and sentence $N+1$ exceeds a statistical threshold (e.g. 95th percentile jump), a new chunk boundary is created.
   - *Trade-off*: Higher preprocessing computation; optimal topic coherence.
4. **Parent-Document / Small-to-Big Retrieval**:
   - *Mechanism*: Index small chunks (e.g. 128 tokens) in the vector store for precision retrieval, but feed the parent document or surrounding section (e.g. 1024 tokens) to the LLM context window.

---

## 4. The RAG Evaluation Triad & Metrics Framework

Enterprise RAG architectures require automated continuous evaluation pipelines (e.g., TruLens, Ragas) to prevent hallucination regressions.

```
                   +------------------------+
                   |       User Query       |
                   +-----------+------------+
                              / \
             Context         /   \         Answer
            Relevance       /     \       Relevance
                           /       \
                          v         v
        +--------------------+   +--------------------+
        |  Retrieved Context |-->| Generated Response |
        +--------------------+   +--------------------+
                              \ /
                               v
                          Faithfulness
                         (Groundedness)
```

### The Three Critical Pillars
1. **Context Relevance (Retrieval Quality)**:
   - *Question*: Did the vector database retrieve passages containing strictly pertinent information without noise?
   - *Metric*: Precision@K, NDCG (Normalized Discounted Cumulative Gain).
2. **Groundedness / Faithfulness (Hallucination Detection)**:
   - *Question*: Can every factual statement in the generated response be mathematically inferred from the retrieved context blocks?
   - *Computation*: LLM-as-a-Judge decomposes the answer into claims and verifies each claim against the context.
3. **Answer Relevance (Query Fulfillment)**:
   - *Question*: Does the generated response directly resolve the user's intent without drifting or evading?
   - *Computation*: Reverse-generate potential questions from the answer and compute semantic embedding similarity against the original query.
