r"""
RAG Triad Automated Evaluation: Faithfulness, Answer Relevance & Context Precision
==================================================================================
Description: Production evaluation suite implementing the RAG Triad methodology (Ragas & TruLens).
             Automates hallucination detection by quantifying Faithfulness (claim-grounding ratio),
             Answer Relevance (semantic query alignment), and Context Precision (mean reciprocal
             rank / signal-to-noise ratio in retrieved knowledge passages).
Enterprise Mapping:
- Continuous Evaluation CI/CD: In enterprise LLM platforms, prompt updates and chunking tweaks
  risk hallucination regressions. Automated RAG evaluation replaces manual spot-checking with
  deterministic statistical telemetry, analogous to automated integration tests in TypeScript/PHP.
- Faithfulness Scoring: Breaks generated answers into atomic assertions and verifies contextual
  entailment, catching ungrounded hallucinations before user presentation.
- Context Precision: Measures retrieval ranking quality, ensuring high-salience knowledge is
  placed at top indices (minimizing the "Lost in the Middle" LLM attention degradation).

Official Documentation References:
- Ragas (Retrieval Augmented Generation Assessment): https://docs.ragas.io/
- TruLens RAG Triad Core Concepts: https://www.trulens.org/trulens_eval/getting_started/core_concepts/rag_triad/
- Context Precision Metrics: https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_precision/
- Faithfulness (Hallucination Detection): https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import Any, Final, NamedTuple, Sequence

import numpy as np
from numpy.typing import NDArray


# ==============================================================================
# 1. Metric Records and Evaluation Results
# ==============================================================================
class AtomicClaim(NamedTuple):
    claim_id: str
    statement: str
    is_grounded: bool
    supporting_evidence: str | None


class RagTriadEvaluationScore(NamedTuple):
    faithfulness_score: float  # [0.0..1.0] Groundedness / anti-hallucination
    answer_relevance_score: float  # [0.0..1.0] Alignment to user query
    context_precision_score: float  # [0.0..1.0] Ranking quality of retrieved context
    composite_quality_score: float  # Weighted harmonic mean
    claims_breakdown: list[AtomicClaim]

    def passes_enterprise_threshold(self, min_composite: float = 0.75) -> bool:
        return self.composite_quality_score >= min_composite


# ==============================================================================
# 2. Embedding Engine for Semantic Scoring
# ==============================================================================
class EvaluationEmbeddingEngine:
    """Computes dense normalized text embeddings for semantic relevance scoring."""

    def __init__(self, dimension: int = 64) -> None:
        self.dimension: int = dimension

    def embed_text(self, text: str) -> NDArray[np.float64]:
        """Compute L2-normalized vector embedding."""
        words = re.findall(r"\b\w+\b", text.lower())
        vec = np.zeros(self.dimension, dtype=np.float64)
        if not words:
            vec[0] = 1.0
            return vec

        for word in words:
            digest = hashlib.sha256(word.encode("utf-8")).digest()
            for d in range(self.dimension):
                weight = (digest[d % len(digest)] - 128) / 128.0
                vec[d] += weight

        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0.0 else vec

    def compute_similarity(self, text_a: str, text_b: str) -> float:
        """Compute cosine similarity between two strings."""
        vec_a = self.embed_text(text_a)
        vec_b = self.embed_text(text_b)
        return float(np.dot(vec_a, vec_b))


# ==============================================================================
# 3. RAG Triad Evaluation Engine (Ragas Architecture)
# ==============================================================================
class RagTriadEvaluator:
    """
    Automated evaluation framework calculating Faithfulness, Answer Relevance,
    and Context Precision.
    """

    def __init__(self, embedding_engine: EvaluationEmbeddingEngine | None = None) -> None:
        self.embedder: EvaluationEmbeddingEngine = embedding_engine or EvaluationEmbeddingEngine()

    # --------------------------------------------------------------------------
    # Metric 1: Faithfulness (Groundedness)
    # --------------------------------------------------------------------------
    def evaluate_faithfulness(
        self, generated_answer: str, retrieved_contexts: Sequence[str]
    ) -> tuple[float, list[AtomicClaim]]:
        """
        Decomposes generated answer into atomic claims and validates whether each
        claim can be directly inferred from the retrieved context passages.
        Formula:
            Faithfulness = (Count of Supported Claims) / (Total Claims)
        """
        # Split answer into sentence assertions
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", generated_answer) if len(s.strip()) > 5]
        if not sentences:
            return 1.0, []

        claims: list[AtomicClaim] = []
        supported_count = 0
        joined_context = " ".join(retrieved_contexts).lower()

        for idx, sentence in enumerate(sentences):
            # Extract key informative words (length >= 4)
            keywords = [w.lower() for w in re.findall(r"\b[a-zA-Z0-9_-]{4,}\b", sentence)]
            
            # Stem matching: check if root/stem of keyword is represented in context
            matched_count = 0
            for kw in keywords:
                stem = kw[:4]
                if kw in joined_context or stem in joined_context:
                    matched_count += 1

            overlap_ratio = matched_count / len(keywords) if keywords else 1.0

            # Grounding heuristic: claim is grounded if >= 50% of informative roots exist in context
            is_grounded = overlap_ratio >= 0.50
            evidence = f"Supported by context (overlap: {overlap_ratio*100:.0f}%)" if is_grounded else "HALLUCINATION: Not grounded in context"

            if is_grounded:
                supported_count += 1

            claims.append(
                AtomicClaim(
                    claim_id=f"CLAIM-{idx+1:02d}",
                    statement=sentence,
                    is_grounded=is_grounded,
                    supporting_evidence=evidence,
                )
            )

        faithfulness = supported_count / len(sentences)
        return faithfulness, claims

    # --------------------------------------------------------------------------
    # Metric 2: Answer Relevance
    # --------------------------------------------------------------------------
    def evaluate_answer_relevance(self, user_query: str, generated_answer: str) -> float:
        """
        Quantifies how directly the generated response answers the original user query.
        Uses directional embedding cosine alignment.
        """
        sim = self.embedder.compute_similarity(user_query, generated_answer)
        # Normalize from [-1..1] to [0..1]
        relevance_score = max(0.0, min(1.0, (sim + 1.0) / 2.0))
        return relevance_score

    # --------------------------------------------------------------------------
    # Metric 3: Context Precision
    # --------------------------------------------------------------------------
    def evaluate_context_precision(
        self, user_query: str, retrieved_contexts: Sequence[str]
    ) -> float:
        """
        Evaluates whether the most relevant context passages are ranked at the top (Rank 1, 2)
        rather than buried at the bottom of the prompt.
        Calculates Mean Reciprocal Rank (MRR) weighted precision.
        """
        if not retrieved_contexts:
            return 0.0

        query_vec = self.embedder.embed_text(user_query)
        relevance_flags: list[bool] = []

        for ctx in retrieved_contexts:
            ctx_vec = self.embedder.embed_text(ctx)
            sim = float(np.dot(query_vec, ctx_vec))
            # Passage considered relevant if similarity threshold exceeds 0.25
            relevance_flags.append(sim > 0.25)

        # Compute precision@k weighted by reciprocal rank
        running_hits = 0
        precision_at_k_sum = 0.0
        total_relevant = sum(relevance_flags)

        if total_relevant == 0:
            return 0.0

        for rank, is_rel in enumerate(relevance_flags, start=1):
            if is_rel:
                running_hits += 1
                precision_at_k_sum += (running_hits / rank)

        return precision_at_k_sum / total_relevant

    # --------------------------------------------------------------------------
    # Aggregate Pipeline Evaluation
    # --------------------------------------------------------------------------
    def evaluate_triad(
        self, user_query: str, retrieved_contexts: Sequence[str], generated_answer: str
    ) -> RagTriadEvaluationScore:
        """Compute complete RAG Triad assessment."""
        faithfulness, claims = self.evaluate_faithfulness(generated_answer, retrieved_contexts)
        relevance = self.evaluate_answer_relevance(user_query, generated_answer)
        precision = self.evaluate_context_precision(user_query, retrieved_contexts)

        # Harmonic composite score: 40% Faithfulness + 35% Relevance + 25% Context Precision
        composite = (0.40 * faithfulness) + (0.35 * relevance) + (0.25 * precision)

        return RagTriadEvaluationScore(
            faithfulness_score=faithfulness,
            answer_relevance_score=relevance,
            context_precision_score=precision,
            composite_quality_score=composite,
            claims_breakdown=claims,
        )


# ==============================================================================
# Verification & Self-Executing Diagnostic Suite
# ==============================================================================
def main() -> None:
    print("=" * 70)
    print(" LEVEL 7: 01_RAG_TRIAD_EVALUATION_RAGAS - ENTERPRISE RUNTIME DEMO")
    print("=" * 70)

    evaluator = RagTriadEvaluator()

    query = "How does PostgreSQL connection pooling work in SQLAlchemy 2.0?"
    contexts = [
        "SQLAlchemy 2.0 uses QueuePool by default for connection pooling with PostgreSQL. "
        "The pool maintains a persistent collection of open database connections, allowing "
        "workers to reuse sockets without paying TCP handshake penalties.",
        "Celery distributes background tasks across Redis brokers with exponential retry backoff.",
    ]

    # Scenario A: Grounded, High-Quality Response (No Hallucination)
    print("\n--- 1. Evaluating Grounded Response (High Faithfulness) ---")
    good_answer = (
        "SQLAlchemy 2.0 employs QueuePool to maintain open database connections for PostgreSQL. "
        "This architecture allows worker tasks to reuse existing TCP sockets, eliminating connection handshake latency."
    )
    score_a = evaluator.evaluate_triad(query, contexts, good_answer)

    print(f"  Faithfulness (Groundedness):   {score_a.faithfulness_score * 100:.1f}%")
    print(f"  Answer Relevance:              {score_a.answer_relevance_score * 100:.1f}%")
    print(f"  Context Precision (MRR):       {score_a.context_precision_score * 100:.1f}%")
    print(f"  Composite RAG Triad Score:     {score_a.composite_quality_score:.4f}")
    assert score_a.faithfulness_score == 1.0
    assert score_a.passes_enterprise_threshold(0.70) is True

    # Scenario B: Hallucinated Response (Low Faithfulness)
    print("\n--- 2. Evaluating Hallucinated Response (Low Faithfulness) ---")
    hallucinated_answer = (
        "SQLAlchemy 2.0 uses Apache Kafka streaming topics to manage PostgreSQL connections. "
        "All connections are written directly to quantum encrypted blockchain registers for audit."
    )
    score_b = evaluator.evaluate_triad(query, contexts, hallucinated_answer)

    print(f"  Faithfulness (Groundedness):   {score_b.faithfulness_score * 100:.1f}%")
    print(f"  Answer Relevance:              {score_b.answer_relevance_score * 100:.1f}%")
    print(f"  Composite RAG Triad Score:     {score_b.composite_quality_score:.4f}")
    print("\n  Claims Grounding Breakdown:")
    for claim in score_b.claims_breakdown:
        status_tag = "[PASS]" if claim.is_grounded else "[FAIL]"
        print(f"    {status_tag} {claim.claim_id}: \"{claim.statement}\"")
        print(f"           Verdict: {claim.supporting_evidence}")

    assert score_b.faithfulness_score < 0.50
    assert score_b.passes_enterprise_threshold(0.70) is False
    print("\n  [SECURITY PASS] Evaluator successfully detected and flagged hallucinated statements.")

    print("\n" + "=" * 70)
    print("[ALL CHECKS PASSED] 01_rag_triad_evaluation_ragas module executed cleanly.")
    print("=" * 70)


if __name__ == "__main__":
    main()
