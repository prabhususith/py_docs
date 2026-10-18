r"""
Machine Learning Pipelines: Vector Mathematics, Scikit-Learn, and Artifact Serialization
========================================================================================
Description: Production machine learning engineering demonstrating vectorized mathematical
             operations in NumPy (dot products, L2 norms, cosine similarity, matrix broadcasting),
             Scikit-Learn declarative preprocessing and classification pipelines (`Pipeline`),
             and persistent binary model artifact serialization via `joblib`.
Enterprise Mapping:
- Vectorized NumPy Arrays: Replaces nested loops in JavaScript and PHP with SIMD-accelerated
  contiguous C/BLAS array buffers. Essential foundation for high-dimensional embedding search.
- Scikit-Learn Pipelines: Encapsulates feature transformation (`StandardScaler`) and estimator
  fitting (`LogisticRegression`) into a single atomic object, eliminating data leakage between
  training and production inference. Analogous to pipeline interceptors in NestJS or middleware chains.
- Joblib Model Serialization: Direct enterprise standard for serializing model weights, scalers,
  and decision boundaries to disk for low-latency production microservice serving.

Official Documentation References:
- Scikit-Learn Pipeline & Composite Estimators: https://scikit-learn.org/stable/modules/compose.html
- NumPy Linear Algebra (linalg): https://numpy.org/doc/stable/reference/routines.linalg.html
- Joblib Model Persistence: https://joblib.readthedocs.io/en/latest/persistence.html
- Scikit-Learn Logistic Regression: https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html
"""

from __future__ import annotations

import os
import tempfile
from typing import Any, Final, NamedTuple

import joblib
import numpy as np
from numpy.typing import NDArray
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


# ==============================================================================
# 1. High-Performance Vector Mathematics in NumPy
# ==============================================================================
class VectorMathEngine:
    """
    Mathematical engine demonstrating linear algebra routines required for
    vector databases, information retrieval, and machine learning feature spaces.
    """

    @staticmethod
    def compute_cosine_similarity(vec_a: NDArray[np.float64], vec_b: NDArray[np.float64]) -> float:
        """
        Compute cosine similarity between two 1-D vectors:
            cos_sim(A, B) = (A . B) / (||A||_2 * ||B||_2)
        Yields value in [-1.0, 1.0], measuring directional orientation regardless of scale.
        """
        dot_product: float = float(np.dot(vec_a, vec_b))
        norm_a: float = float(np.linalg.norm(vec_a))
        norm_b: float = float(np.linalg.norm(vec_b))

        if norm_a == 0.0 or norm_b == 0.0:
            raise ValueError("Cosine similarity is undefined for zero-magnitude vectors.")

        return dot_product / (norm_a * norm_b)

    @staticmethod
    def batch_cosine_similarity(
        query_vector: NDArray[np.float64], candidate_matrix: NDArray[np.float64]
    ) -> NDArray[np.float64]:
        """
        Compute cosine similarity between a single query vector and N candidate vectors
        simultaneously using SIMD matrix broadcasting.
        """
        # Dot product against all rows: shape (N,)
        dot_products: NDArray[np.float64] = candidate_matrix @ query_vector

        # L2 norm of query: scalar
        query_norm: float = float(np.linalg.norm(query_vector))

        # L2 norm of all candidate rows: shape (N,)
        candidate_norms: NDArray[np.float64] = np.linalg.norm(candidate_matrix, axis=1)

        denominator: NDArray[np.float64] = candidate_norms * query_norm
        # Guard against zero-division
        zero_mask = denominator == 0.0
        denominator[zero_mask] = 1e-12

        return dot_products / denominator


# ==============================================================================
# 2. Production Scikit-Learn ML Pipeline Architecture
# ==============================================================================
class ChurnPredictionResult(NamedTuple):
    pipeline: Pipeline
    accuracy: float
    roc_auc: float
    test_samples: int


class ChurnModelPipelineFactory:
    """
    Enterprise factory responsible for constructing, training, evaluating,
    and persisting production Scikit-Learn pipelines.
    """

    @staticmethod
    def build_pipeline() -> Pipeline:
        """
        Construct atomic Scikit-Learn Pipeline:
        Step 1: StandardScaler - transforms features to zero mean and unit variance
        Step 2: LogisticRegression - regularized linear classification estimator
        """
        return Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                (
                    "classifier",
                    LogisticRegression(
                        C=1.0,
                        solver="lbfgs",
                        max_iter=500,
                        random_state=42,
                    ),
                ),
            ]
        )

    @classmethod
    def train_and_evaluate(
        cls, X: NDArray[np.float64], y: NDArray[np.int64]
    ) -> tuple[ChurnPredictionResult, tuple[NDArray[np.float64], NDArray[np.int64]]]:
        """Train pipeline, evaluate generalization metrics, and return evaluation pack."""
        # Split into training and holdout validation sets (80/20)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.20, random_state=42, stratify=y
        )

        pipeline: Pipeline = cls.build_pipeline()
        # Atomic fit: fits scaler and estimator sequentially without leakage
        pipeline.fit(X_train, y_train)

        # Inference on holdout set
        y_pred: NDArray[np.int64] = pipeline.predict(X_test)
        y_proba: NDArray[np.float64] = pipeline.predict_proba(X_test)[:, 1]

        acc: float = float(accuracy_score(y_test, y_pred))
        auc: float = float(roc_auc_score(y_test, y_proba))

        return (
            ChurnPredictionResult(
                pipeline=pipeline,
                accuracy=acc,
                roc_auc=auc,
                test_samples=len(y_test),
            ),
            (X_test, y_test),
        )


# ==============================================================================
# 3. Model Artifact Serialization & Deserialization (Joblib)
# ==============================================================================
class ModelArtifactManager:
    """Manages versioned persistence and validation of trained pipeline artifacts."""

    @staticmethod
    def serialize(pipeline: Pipeline, output_path: str) -> str:
        """Serialize complete pipeline (transformers + estimator) to compressed binary."""
        # Compress level 3 provides optimal balance of speed and archive size
        joblib.dump(pipeline, output_path, compress=3)
        return output_path

    @staticmethod
    def deserialize(artifact_path: str) -> Pipeline:
        """Deserialize and validate model artifact from disk."""
        if not os.path.exists(artifact_path):
            raise FileNotFoundError(f"Model artifact not found at: {artifact_path}")
        pipeline = joblib.load(artifact_path)
        if not isinstance(pipeline, Pipeline):
            raise TypeError("Loaded artifact is not a valid Scikit-Learn Pipeline instance.")
        return pipeline


# ==============================================================================
# Verification & Self-Executing Diagnostic Suite
# ==============================================================================
def main() -> None:
    print("=" * 70)
    print(" LEVEL 5: 01_NUMPY_SCIKIT_ML_PIPELINE - ENTERPRISE RUNTIME DEMO")
    print("=" * 70)

    # 1. Verify Vector Mathematics
    print("\n--- 1. NumPy Vector Mathematics & Cosine Similarity ---")
    query_vec: Final[NDArray[np.float64]] = np.array([0.2, 0.8, -0.5, 0.9], dtype=np.float64)
    target_vec: Final[NDArray[np.float64]] = np.array([0.25, 0.75, -0.4, 0.85], dtype=np.float64)
    orthogonal_vec: Final[NDArray[np.float64]] = np.array([0.0, 0.0, 0.0, 0.0], dtype=np.float64)

    cos_sim = VectorMathEngine.compute_cosine_similarity(query_vec, target_vec)
    print(f"  Single Pair Cosine Similarity: {cos_sim:.5f}")
    assert cos_sim > 0.95  # Highly similar directional alignment

    # Batch cosine similarity against 10,000 candidate embeddings
    candidate_embeddings: Final[NDArray[np.float64]] = np.random.randn(10_000, 4).astype(np.float64)
    batch_scores = VectorMathEngine.batch_cosine_similarity(query_vec, candidate_embeddings)
    print(f"  Batch Sim Computation over 10,000 vectors: Mean={np.mean(batch_scores):.4f}, Max={np.max(batch_scores):.4f}")
    assert batch_scores.shape == (10_000,)

    # 2. Train Scikit-Learn Enterprise Pipeline
    print("\n--- 2. Scikit-Learn Pipeline Training & Validation ---")
    # Synthesize realistic enterprise churn feature matrix: 1,000 users, 10 features
    X, y = make_classification(
        n_samples=1000,
        n_features=10,
        n_informative=6,
        n_redundant=2,
        n_classes=2,
        weights=[0.70, 0.30],  # Imbalanced 70/30 churn ratio
        random_state=42,
    )
    X = X.astype(np.float64)
    y = y.astype(np.int64)

    eval_result, (X_test, y_test) = ChurnModelPipelineFactory.train_and_evaluate(X, y)
    print(f"  Evaluated on {eval_result.test_samples} Holdout Samples:")
    print(f"  Generalization Accuracy: {eval_result.accuracy * 100:.2f}%")
    print(f"  ROC-AUC Score:           {eval_result.roc_auc:.4f}")
    assert eval_result.accuracy > 0.70
    assert eval_result.roc_auc > 0.70

    # 3. Model Persistence (Joblib Serialization)
    print("\n--- 3. Joblib Model Serialization & Deterministic Inference ---")
    with tempfile.TemporaryDirectory() as tmp_dir:
        model_filepath = os.path.join(tmp_dir, "customer_churn_pipeline_v1.joblib")
        ModelArtifactManager.serialize(eval_result.pipeline, model_filepath)
        print(f"  Saved compressed model artifact to: {model_filepath}")
        print(f"  Artifact File Size: {os.path.getsize(model_filepath):,} bytes")

        # Reload model
        loaded_pipeline = ModelArtifactManager.deserialize(model_filepath)
        print("  Reloaded model artifact into memory.")

        # Assert identical predictions between in-memory and deserialized model
        orig_preds = eval_result.pipeline.predict_proba(X_test[:5])
        loaded_preds = loaded_pipeline.predict_proba(X_test[:5])
        np.testing.assert_allclose(orig_preds, loaded_preds, rtol=1e-6)
        print("  [PASS] Deserialized model predictions strictly identical to original pipeline.")

    print("\n" + "=" * 70)
    print("[ALL CHECKS PASSED] 01_numpy_scikit_ml_pipeline module executed cleanly.")
    print("=" * 70)


if __name__ == "__main__":
    main()
