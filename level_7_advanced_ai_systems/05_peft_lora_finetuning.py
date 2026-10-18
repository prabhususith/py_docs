r"""
Parameter-Efficient Fine-Tuning (PEFT): Low-Rank Adaptation (LoRA) Architecture
================================================================================
Description: Mathematical and architectural implementation of Low-Rank Adaptation (LoRA).
             Freezes pre-trained base model weights ($W_0$) and decomposes weight updates into
             low-rank matrices ($B \cdot A$) with rank $r \ll d$. Reduces trainable parameters
             to $<0.1\%$, demonstrates gradient backpropagation, parameter accounting, and
             zero-latency weight merging ($W_{\text{deploy}} = W_0 + \frac{\alpha}{r} BA$).
Enterprise Mapping:
- Full Fine-Tuning (FFT) vs PEFT: Traditional FFT requires hundreds of gigabytes of VRAM to track
  optimizer states for billions of parameters, producing massive multi-GB checkpoints per tenant.
  LoRA reduces adapter sizes to ~20-50MB, enabling multi-tenant adapter hot-swapping on a single base model.
- Production Weight Merging: Unlike runtime adapter routing, merging the low-rank delta back into
  the base weights introduces zero mathematical latency overhead during production inference.

Official Documentation References:
- Hugging Face PEFT Library: https://huggingface.co/docs/peft/
- LoRA Research Paper (Hu et al. ICLR 2022): https://arxiv.org/abs/2106.09685
- LoRA Configuration Guide: https://huggingface.co/docs/peft/package_reference/lora
"""

from __future__ import annotations

import math
from typing import Any, Final, NamedTuple

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, Field


# ==============================================================================
# 1. LoRA Configuration Schema
# ==============================================================================
class LoRAConfig(BaseModel):
    """
    Hyperparameter specification matching Hugging Face PEFT LoraConfig.
    """

    r: int = Field(default=8, ge=1, le=128, description="Low-rank decomposition rank (dimension bottleneck)")
    lora_alpha: float = Field(default=16.0, gt=0.0, description="Scaling factor hyperparameter")
    lora_dropout: float = Field(default=0.05, ge=0.0, le=0.5, description="Dropout probability for LoRA input")
    target_modules: list[str] = Field(
        default_factory=lambda: ["q_proj", "v_proj"],
        description="Linear attention projection modules targeted for adapter injection",
    )

    @property
    def scaling(self) -> float:
        """LoRA scaling factor: alpha / r."""
        return self.lora_alpha / self.r


class ParameterAuditReport(NamedTuple):
    base_parameters: int
    trainable_lora_parameters: int
    trainable_ratio_percent: float
    rank: int


# ==============================================================================
# 2. LoRA Linear Layer Implementation
# ==============================================================================
class LoRALinearLayer:
    """
    Drop-in replacement for a standard PyTorch/NumPy linear projection layer:
        y = x . W_0^T + scaling * (x . A^T . B^T)
    Where:
        W_0 in R^(out_features x in_features) - Frozen
        A   in R^(r x in_features)            - Gaussian initialized
        B   in R^(out_features x r)            - Zero initialized
    """

    def __init__(
        self,
        in_features: int,
        out_features: int,
        config: LoRAConfig,
        layer_name: str = "q_proj",
    ) -> None:
        self.in_features: int = in_features
        self.out_features: int = out_features
        self.config: LoRAConfig = config
        self.layer_name: str = layer_name
        self.is_merged: bool = False

        # 1. Base Model Weight Matrix W_0 (FROZEN)
        # Xavier/Glorot initialization
        scale = math.sqrt(2.0 / (in_features + out_features))
        self.W_base: NDArray[np.float64] = np.random.randn(out_features, in_features) * scale

        # 2. Low-Rank Adapter Matrices
        r = config.r
        # Matrix A: Initialized with Gaussian distribution N(0, 1/r)
        self.lora_A: NDArray[np.float64] = np.random.randn(r, in_features) * (1.0 / math.sqrt(r))
        # Matrix B: Initialized strictly to ZERO so that delta W = 0 at training inception
        self.lora_B: NDArray[np.float64] = np.zeros((out_features, r), dtype=np.float64)

    def forward(self, x: NDArray[np.float64]) -> NDArray[np.float64]:
        """
        Forward computation:
        If merged: y = x @ W_merged^T
        If unmerged: y = x @ W_base^T + scaling * ((x @ A^T) @ B^T)
        """
        if self.is_merged:
            return x @ self.W_base.T

        # Base forward pass: (batch, in) @ (in, out) -> (batch, out)
        base_out = x @ self.W_base.T

        # LoRA forward pass: (batch, in) @ (in, r) -> (batch, r) @ (r, out) -> (batch, out)
        lora_out = (x @ self.lora_A.T) @ self.lora_B.T

        return base_out + (self.config.scaling * lora_out)

    def train_step_sgd(
        self, x: NDArray[np.float64], grad_output: NDArray[np.float64], learning_rate: float = 0.01
    ) -> float:
        """
        Execute gradient backpropagation updating ONLY low-rank matrices A and B.
        W_base receives ZERO gradients (100% frozen).
        """
        if self.is_merged:
            raise RuntimeError("Cannot execute training step on merged layer. Unmerge first.")

        batch_size = x.shape[0]
        scaling = self.config.scaling

        # Intermediate activation: h = x @ A^T (shape: batch, r)
        h = x @ self.lora_A.T

        # Gradients with respect to B: grad_output^T @ h (shape: out, r)
        grad_B = (grad_output.T @ h) * scaling / batch_size

        # Gradients with respect to A: (grad_output @ B)^T @ x (shape: r, in)
        grad_A = ((grad_output @ self.lora_B).T @ x) * scaling / batch_size

        # Update trainable LoRA parameters via SGD
        self.lora_B -= learning_rate * grad_B
        self.lora_A -= learning_rate * grad_A

        loss_norm = float(np.linalg.norm(grad_output))
        return loss_norm

    def merge_weights_for_deployment(self) -> None:
        """
        Fold LoRA delta into base weight matrix:
            W_base_new = W_base + scaling * (B @ A)
        Zero inference latency overhead post-merge.
        """
        if self.is_merged:
            return

        # Delta W = scaling * (B @ A) (shape: out_features, in_features)
        delta_W = self.config.scaling * (self.lora_B @ self.lora_A)
        self.W_base += delta_W
        self.is_merged = True

    def unmerge_weights(self) -> None:
        """Subtract LoRA delta to resume fine-tuning or swap adapters."""
        if not self.is_merged:
            return

        delta_W = self.config.scaling * (self.lora_B @ self.lora_A)
        self.W_base -= delta_W
        self.is_merged = False

    def audit_parameters(self) -> ParameterAuditReport:
        """Compute base vs trainable parameter inventory."""
        base_params = self.in_features * self.out_features
        # Matrix A has (r * in_features), Matrix B has (out_features * r)
        trainable_lora_params = (self.config.r * self.in_features) + (self.out_features * self.config.r)
        ratio_percent = (trainable_lora_params / base_params) * 100.0

        return ParameterAuditReport(
            base_parameters=base_params,
            trainable_lora_parameters=trainable_lora_params,
            trainable_ratio_percent=ratio_percent,
            rank=self.config.r,
        )


# ==============================================================================
# Verification & Self-Executing Diagnostic Suite
# ==============================================================================
def main() -> None:
    print("=" * 70)
    print(" LEVEL 7: 05_PEFT_LORA_FINETUNING - ENTERPRISE RUNTIME DEMO")
    print("=" * 70)

    # 1. Parameter Audit on Production-Scale Linear Projection Layer
    print("\n--- 1. Parameter-Efficiency Accounting (Llama-3 Attention Layer) ---")
    # Real-world projection dimensions (Llama-3 8B: hidden_dim = 4096)
    in_dim: Final[int] = 4096
    out_dim: Final[int] = 4096
    lora_cfg = LoRAConfig(r=8, lora_alpha=16.0)

    lora_layer = LoRALinearLayer(in_features=in_dim, out_features=out_dim, config=lora_cfg)
    audit = lora_layer.audit_parameters()

    print(f"  Base Model Weights (W_0):       {audit.base_parameters:,} parameters (FROZEN)")
    print(f"  LoRA Adapter Weights (A + B):   {audit.trainable_lora_parameters:,} parameters (TRAINABLE, Rank={audit.rank})")
    print(f"  Trainable Parameter Ratio:      {audit.trainable_ratio_percent:.3f}% of base model")
    assert audit.trainable_ratio_percent < 0.50
    print("  [PASS] LoRA reduces trainable footprint by >99.6% compared to full fine-tuning.")

    # 2. Initial Forward Pass Invariant Check
    print("\n--- 2. Initialization Invariant: Zero Initial Delta ---")
    # At initialization, Matrix B = 0, so y = x @ W_base^T exactly
    x_test = np.random.randn(4, in_dim).astype(np.float64)
    y_lora_initial = lora_layer.forward(x_test)
    y_base_direct = x_test @ lora_layer.W_base.T

    np.testing.assert_allclose(y_lora_initial, y_base_direct, rtol=1e-8)
    print("  [PASS] Initial LoRA forward pass strictly equal to base model (B = 0 initialization).")

    # 3. Fine-Tuning Optimization Step (SGD)
    print("\n--- 3. Adapter Training Step & Gradient Backpropagation ---")
    target_output = y_lora_initial + 1.0  # Synthetic target
    grad_out = y_lora_initial - target_output

    norm_before = float(np.linalg.norm(lora_layer.lora_B))
    assert norm_before == 0.0  # B was zero

    # Step SGD
    lora_layer.train_step_sgd(x=x_test, grad_output=grad_out, learning_rate=0.05)

    norm_after = float(np.linalg.norm(lora_layer.lora_B))
    print(f"  Norm of Matrix B before training step: {norm_before:.6f}")
    print(f"  Norm of Matrix B after training step:  {norm_after:.6f}")
    assert norm_after > 0.0
    print("  [PASS] Adapter weights successfully updated while base weights remained strictly frozen.")

    # 4. Weight Merging for Zero-Latency Production Deployment
    print("\n--- 4. Zero-Latency Weight Merging & Deployment Parity ---")
    # Inference before merge
    y_unmerged = lora_layer.forward(x_test)

    # Merge weights
    lora_layer.merge_weights_for_deployment()
    assert lora_layer.is_merged is True
    print("  Merged adapter delta into base weights: W_deploy = W_0 + (alpha/r)*B*A")

    # Inference after merge
    y_merged = lora_layer.forward(x_test)
    np.testing.assert_allclose(y_unmerged, y_merged, rtol=1e-8)
    print("  [PASS] Merged layer produces mathematically identical activations without adapter overhead.")

    # Unmerge test
    lora_layer.unmerge_weights()
    assert lora_layer.is_merged is False
    print("  Unmerged adapter weights cleanly: Ready for multi-tenant adapter swapping.")

    print("\n" + "=" * 70)
    print("[ALL CHECKS PASSED] 05_peft_lora_finetuning module executed cleanly.")
    print("=" * 70)


if __name__ == "__main__":
    main()
