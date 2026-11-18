"""
Oxford Publication Illustrator: High-DPI Diagram Engine for Ebook
=================================================================
Generates 10 publication-quality diagrams, charts, and intuitive real-time
flowcharts designed to bridge age-10+ intuition with staff architect rigor.
"""

from __future__ import annotations

import os
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# Ensure assets directory
ASSETS_DIR = Path("book_assets")
ASSETS_DIR.mkdir(exist_ok=True)

# Oxford Academic Color Palette
OXFORD_NAVY = "#002147"
CRIMSON = "#8B0000"
ACCENT_GOLD = "#D4AF37"
SLATE_DARK = "#2C3E50"
SOFT_GREY = "#ECF0F1"
EMERALD_GREEN = "#27AE60"
CORAL_RED = "#E74C3C"
ROYAL_BLUE = "#2980B9"
AMBER_ORANGE = "#E67E22"
PURPLE = "#8E44AD"

plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]


def fig_01_deque_vs_list():
    """Diagram 1: Cafeteria Tray Line (O(1) Deque) vs Domino Shuffling (O(N) List)."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")

    # Left: list.pop(0) - Shuffling Dominoes
    ax1.set_facecolor("#FCF8F8")
    ax1.set_title("Python list.pop(0)  [The Domino Shuffle: O(N)]", fontsize=11, fontweight="bold", color=CRIMSON, pad=12)
    ax1.text(0.5, 0.88, "Popping the front item forces EVERY SINGLE item\nto shift left in memory! (66x slower)",
             ha="center", va="center", fontsize=8.5, color=SLATE_DARK, transform=ax1.transAxes)

    # Draw boxes
    for i in range(5):
        rect = patches.FancyBboxPatch((0.1 + i * 0.16, 0.45), 0.13, 0.22,
                                     boxstyle="round,pad=0.02,rounding_size=0.03",
                                     facecolor="#FADBD8" if i == 0 else "#EAEDED",
                                     edgecolor=CORAL_RED if i == 0 else "#BDC3C7", linewidth=1.5)
        ax1.add_patch(rect)
        label = "POP!\n(Del)" if i == 0 else f"Item {i}\n-> shft"
        ax1.text(0.1 + i * 0.16 + 0.065, 0.56, label, ha="center", va="center", fontsize=8,
                 fontweight="bold" if i == 0 else "normal", color=CORAL_RED if i == 0 else SLATE_DARK)

    # Shift arrows
    for i in range(1, 5):
        ax1.annotate("", xy=(0.1 + (i-1)*0.16 + 0.13, 0.4), xytext=(0.1 + i*0.16 + 0.05, 0.4),
                     arrowprops=dict(arrowstyle="->", color=CORAL_RED, lw=1.5))
    ax1.text(0.5, 0.2, "100,000 items = 100,000 memory moves every pop!", ha="center", fontsize=8, color=CORAL_RED, style="italic")
    ax1.axis("off")

    # Right: collections.deque - The Cafeteria Tray Line
    ax2.set_facecolor("#F4FBF7")
    ax2.set_title("collections.deque  [The Cafeteria Line: O(1)]", fontsize=11, fontweight="bold", color=EMERALD_GREEN, pad=12)
    ax2.text(0.5, 0.88, "Doubly-linked 64-item blocks. Popping front or back\njust moves a tiny pointer! Zero items shift!",
             ha="center", va="center", fontsize=8.5, color=SLATE_DARK, transform=ax2.transAxes)

    for i in range(4):
        rect = patches.FancyBboxPatch((0.12 + i * 0.2, 0.45), 0.16, 0.22,
                                     boxstyle="round,pad=0.02,rounding_size=0.03",
                                     facecolor="#D4EFDF", edgecolor=EMERALD_GREEN, linewidth=1.5)
        ax2.add_patch(rect)
        ax2.text(0.12 + i * 0.2 + 0.08, 0.56, f"Block {i+1}\n[64 Items]", ha="center", va="center",
                 fontsize=8, fontweight="bold", color=OXFORD_NAVY)

    # Double arrows connecting blocks
    for i in range(3):
        ax2.annotate("", xy=(0.12 + (i+1)*0.2, 0.56), xytext=(0.12 + i*0.2 + 0.16, 0.56),
                     arrowprops=dict(arrowstyle="<->", color=EMERALD_GREEN, lw=2))

    ax2.annotate("O(1) Pop Front", xy=(0.2, 0.7), xytext=(0.2, 0.82),
                 arrowprops=dict(arrowstyle="->", color=EMERALD_GREEN, lw=1.5),
                 ha="center", fontsize=8, fontweight="bold", color=EMERALD_GREEN)
    ax2.annotate("O(1) Append", xy=(0.8, 0.7), xytext=(0.8, 0.82),
                 arrowprops=dict(arrowstyle="->", color=EMERALD_GREEN, lw=1.5),
                 ha="center", fontsize=8, fontweight="bold", color=EMERALD_GREEN)

    ax2.text(0.5, 0.2, "Instant O(1) Speedup: 66.7x Faster than list.pop(0)!", ha="center", fontsize=8, color=EMERALD_GREEN, fontweight="bold")
    ax2.axis("off")

    plt.tight_layout()
    plt.savefig(ASSETS_DIR / "fig_01_deque_vs_list.png", bbox_inches="tight")
    plt.close()


def fig_02_heap_tree_vs_array():
    """Diagram 2: Binary Min-Heap: Concept Tree vs Flat Contiguous Array."""
    fig, ax = plt.subplots(figsize=(9, 4.5), dpi=300)
    ax.set_facecolor("#FAFAFA")
    ax.set_title("Binary Min-Heap: Tree Concept vs High-Speed Contiguous C-Array", fontsize=11, fontweight="bold", color=OXFORD_NAVY, pad=14)

    # Tree Nodes: [10 (root), 20 (L), 15 (R), 30 (LL), 40 (LR), 50 (RL), 25 (RR)]
    coords = {
        0: (0.5, 0.85, "10 [Min]"),
        1: (0.3, 0.62, "20"),
        2: (0.7, 0.62, "15"),
        3: (0.2, 0.40, "30"),
        4: (0.4, 0.40, "40"),
        5: (0.6, 0.40, "50"),
        6: (0.8, 0.40, "25"),
    }
    edges = [(0, 1), (0, 2), (1, 3), (1, 4), (2, 5), (2, 6)]

    # Draw edges
    for u, v in edges:
        x1, y1, _ = coords[u]
        x2, y2, _ = coords[v]
        ax.plot([x1, x2], [y1, y2], color="#BDC3C7", lw=2, zorder=1)

    # Draw nodes
    for idx, (x, y, label) in coords.items():
        circle = plt.Circle((x, y), 0.045, facecolor="#EBF5FB" if idx > 0 else "#D4EFDF",
                            edgecolor=ROYAL_BLUE if idx > 0 else EMERALD_GREEN, linewidth=2, zorder=2)
        ax.add_patch(circle)
        ax.text(x, y, label, ha="center", va="center", fontsize=8, fontweight="bold",
                color=OXFORD_NAVY if idx > 0 else EMERALD_GREEN, zorder=3)

    # Memory Array Representation at the bottom
    ax.text(0.5, 0.22, "Actual Physical Memory Layout in Python (Flat list in C)", ha="center", fontsize=9, fontweight="bold", color=SLATE_DARK)

    items = ["10", "20", "15", "30", "40", "50", "25"]
    for i, val in enumerate(items):
        rx = 0.18 + i * 0.09
        rect = patches.Rectangle((rx, 0.06), 0.08, 0.1, facecolor="#FEF9E7", edgecolor=ACCENT_GOLD, lw=1.5)
        ax.add_patch(rect)
        ax.text(rx + 0.04, 0.11, val, ha="center", va="center", fontsize=9, fontweight="bold", color=OXFORD_NAVY)
        ax.text(rx + 0.04, 0.02, f"idx {i}", ha="center", va="center", fontsize=7.5, color="#7F8C8D")

    ax.text(0.5, -0.05, "Parent: (i-1) // 2  |  Left Child: 2i + 1  |  Right Child: 2i + 2  (Zero Pointer Overhead!)",
            ha="center", fontsize=8, style="italic", color=OXFORD_NAVY)

    ax.set_xlim(0.05, 0.95)
    ax.set_ylim(-0.08, 0.95)
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(ASSETS_DIR / "fig_02_heap_tree_vs_array.png", bbox_inches="tight")
    plt.close()


def fig_03_oop_metaclass_lifecycle():
    """Diagram 3: The Metaclass Factory & Class Creation Lifecycle."""
    fig, ax = plt.subplots(figsize=(9, 4.2), dpi=300)
    ax.set_facecolor("#FFFFFF")
    ax.set_title("The Master Blueprint: Python Metaclass & Class Creation Lifecycle", fontsize=11, fontweight="bold", color=OXFORD_NAVY, pad=12)

    stages = [
        ("1. Metaclass `__new__`", "Intercepts class name, bases,\nand dictionary before creation.\nValidates business rules.", "#E8F8F5", EMERALD_GREEN),
        ("2. Metaclass `__init__`", "Allocates the Class Object\nin memory. Registers in\nglobal entity catalogs.", "#EBF5FB", ROYAL_BLUE),
        ("3. `__init_subclass__`", "PEP 487 Hook: Child class\nnotifies base without heavy\nmetaclass overhead.", "#FEF9E7", AMBER_ORANGE),
        ("4. Instance `__call__`", "User calls `User(id=1)`.\nTriggers `__new__` (allocation)\nthen `__init__` (assignment).", "#F4ECF7", PURPLE),
    ]

    for i, (title, desc, bg, border) in enumerate(stages):
        x = 0.05 + i * 0.235
        rect = patches.FancyBboxPatch((x, 0.25), 0.205, 0.55,
                                     boxstyle="round,pad=0.02,rounding_size=0.03",
                                     facecolor=bg, edgecolor=border, linewidth=2)
        ax.add_patch(rect)
        ax.text(x + 0.1025, 0.70, title, ha="center", va="center", fontsize=8.5, fontweight="bold", color=border)
        ax.text(x + 0.1025, 0.45, desc, ha="center", va="center", fontsize=7.5, color=SLATE_DARK)

        if i < 3:
            ax.annotate("", xy=(x + 0.205 + 0.03, 0.52), xytext=(x + 0.205, 0.52),
                        arrowprops=dict(arrowstyle="->", color=OXFORD_NAVY, lw=2))

    ax.text(0.5, 0.08, "Kid Intuition: A Metaclass is the Lego Mold Maker that makes the molds that stamp out the Lego bricks!",
            ha="center", fontsize=8.5, fontweight="bold", color=CRIMSON, style="italic")

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 0.9)
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(ASSETS_DIR / "fig_03_oop_metaclass_lifecycle.png", bbox_inches="tight")
    plt.close()


def fig_04_numpy_strides_simd():
    """Diagram 4: NumPy Contiguous C-Strides & SIMD vs Python Pointer Overhead."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.2), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")

    # Left: Pure Python List
    ax1.set_facecolor("#FDF7F7")
    ax1.set_title("Standard Python List: Pointer Chasing", fontsize=10.5, fontweight="bold", color=CORAL_RED, pad=10)
    ax1.text(0.5, 0.85, "Array of pointers pointing to scattered PyObject memory boxes\n(High GC overhead, pointer cache misses)",
             ha="center", fontsize=8, color=SLATE_DARK, transform=ax1.transAxes)

    for i in range(4):
        # Pointer slot
        rect = patches.Rectangle((0.15 + i*0.2, 0.5), 0.14, 0.15, facecolor="#EAEDED", edgecolor="#7F8C8D", lw=1.2)
        ax1.add_patch(rect)
        ax1.text(0.15 + i*0.2 + 0.07, 0.575, f"Ptr {i}", ha="center", va="center", fontsize=7.5, color="#2C3E50")

        # Object box scattered
        oy = 0.2 + (0.1 if i % 2 == 0 else -0.05)
        orect = patches.Rectangle((0.15 + i*0.2, oy), 0.14, 0.12, facecolor="#FADBD8", edgecolor=CORAL_RED, lw=1.2)
        ax1.add_patch(orect)
        ax1.text(0.15 + i*0.2 + 0.07, oy + 0.06, f"Int: {i*10}\n[28 Bytes!]", ha="center", va="center", fontsize=7, color=CRIMSON)

        # Arrow
        ax1.annotate("", xy=(0.15 + i*0.2 + 0.07, oy + 0.12), xytext=(0.15 + i*0.2 + 0.07, 0.5),
                     arrowprops=dict(arrowstyle="->", color=CORAL_RED, lw=1.2))

    ax1.axis("off")

    # Right: NumPy ndarray
    ax2.set_facecolor("#F4FAF6")
    ax2.set_title("NumPy ndarray: SIMD Vectorization (11.9x Speedup)", fontsize=10.5, fontweight="bold", color=EMERALD_GREEN, pad=10)
    ax2.text(0.5, 0.85, "Single continuous C-memory block with mathematical strides\nCPU AVX2/AVX-512 processes 4-8 numbers simultaneously!",
             ha="center", fontsize=8, color=SLATE_DARK, transform=ax2.transAxes)

    # Contiguous strip
    rect = patches.Rectangle((0.1, 0.45), 0.8, 0.22, facecolor="#D4EFDF", edgecolor=EMERALD_GREEN, lw=2)
    ax2.add_patch(rect)

    for i in range(5):
        ax2.plot([0.1 + i*0.16, 0.1 + i*0.16], [0.45, 0.67], color=EMERALD_GREEN, lw=1.5)
        ax2.text(0.1 + i*0.16 + 0.08, 0.56, f"{i*10}\n[int64: 8B]", ha="center", va="center", fontsize=8, fontweight="bold", color=OXFORD_NAVY)

    ax2.annotate("SIMD AVX-512 Vector Register (Calculates ALL at once!)", xy=(0.5, 0.67), xytext=(0.5, 0.8),
                 arrowprops=dict(arrowstyle="->", color=EMERALD_GREEN, lw=2),
                 ha="center", fontsize=8, fontweight="bold", color=EMERALD_GREEN)
    ax2.axis("off")

    plt.tight_layout()
    plt.savefig(ASSETS_DIR / "fig_04_numpy_strides_simd.png", bbox_inches="tight")
    plt.close()


def fig_05_clean_architecture_onion():
    """Diagram 5: The Onion of Clean DDD Architecture."""
    fig, ax = plt.subplots(figsize=(8.5, 5), dpi=300)
    ax.set_facecolor("#FFFFFF")
    ax.set_title("The Fortress of Clean Architecture: Dependency Inversion Rule", fontsize=11, fontweight="bold", color=OXFORD_NAVY, pad=14)

    # Concentric circles
    circles = [
        (0.42, "#EBF5FB", ROYAL_BLUE, "Outer Ring: Frameworks & Drivers\n(FastAPI, Uvicorn, SQLite, Redis, Celery)"),
        (0.31, "#FEF9E7", AMBER_ORANGE, "Interface Adapters & Controllers\n(Repositories, DTOs, Serializers, Schemas)"),
        (0.20, "#E8F8F5", EMERALD_GREEN, "Application Use Cases\n(CreateOrder, AuthenticateUser, StreamTokens)"),
        (0.10, "#FDEDEC", CRIMSON, "Domain Entities\n(Pure Logic)"),
    ]

    for radius, bg, border, label in circles:
        c = plt.Circle((0.5, 0.5), radius, facecolor=bg, edgecolor=border, lw=2)
        ax.add_patch(c)

    # Annotations
    ax.text(0.5, 0.5, "DOMAIN\nENTITIES\n(Zero Deps)", ha="center", va="center", fontsize=8, fontweight="bold", color=CRIMSON)
    ax.text(0.5, 0.65, "Application Use Cases", ha="center", va="center", fontsize=8, fontweight="bold", color=EMERALD_GREEN)
    ax.text(0.5, 0.76, "Interface Adapters (FastAPI / Repos)", ha="center", va="center", fontsize=8, fontweight="bold", color=AMBER_ORANGE)
    ax.text(0.5, 0.87, "Frameworks & Drivers (WebSockets, Celery, Postgres)", ha="center", va="center", fontsize=8, fontweight="bold", color=ROYAL_BLUE)

    # Dependency arrow pointing inwards
    ax.annotate("Dependencies MUST ONLY point inward ->", xy=(0.82, 0.5), xytext=(0.95, 0.5),
                arrowprops=dict(arrowstyle="->", color=OXFORD_NAVY, lw=2.5),
                ha="center", va="center", fontsize=8.5, fontweight="bold", color=OXFORD_NAVY, rotation=90)

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(ASSETS_DIR / "fig_05_clean_architecture_onion.png", bbox_inches="tight")
    plt.close()


def fig_06_rag_vector_search():
    """Diagram 6: The Detective's Meaning-Magnets: High-Dimensional RAG & ChromaDB."""
    fig, ax = plt.subplots(figsize=(9, 4.5), dpi=300)
    ax.set_facecolor("#FCFDFD")
    ax.set_title("The Detective's Meaning-Magnets: High-Dimensional Vector Embeddings & RAG", fontsize=11, fontweight="bold", color=OXFORD_NAVY, pad=12)

    # Vector Space Scatter
    np.random.seed(42)
    # Cluster 1: Database
    x1 = np.random.normal(0.25, 0.05, 8)
    y1 = np.random.normal(0.65, 0.06, 8)
    ax.scatter(x1, y1, color=ROYAL_BLUE, s=80, alpha=0.8, edgecolors="none", label="Cluster A: SQL & Databases")

    # Cluster 2: AI & LLMs
    x2 = np.random.normal(0.70, 0.05, 8)
    y2 = np.random.normal(0.70, 0.06, 8)
    ax.scatter(x2, y2, color=EMERALD_GREEN, s=80, alpha=0.8, edgecolors="none", label="Cluster B: Neural Nets & Agents")

    # Cluster 3: Security
    x3 = np.random.normal(0.50, 0.06, 8)
    y3 = np.random.normal(0.25, 0.05, 8)
    ax.scatter(x3, y3, color=CRIMSON, s=80, alpha=0.8, edgecolors="none", label="Cluster C: Cryptography & Firewalls")

    # User Query Point
    qx, qy = 0.68, 0.65
    ax.scatter([qx], [qy], color=ACCENT_GOLD, s=200, marker="*", edgecolors=OXFORD_NAVY, lw=1.5, zorder=5, label="User Query: 'How to serve vLLM?'")

    # Top-K circle around query
    circle = plt.Circle((qx, qy), 0.12, facecolor="#FEF9E7", edgecolor=ACCENT_GOLD, linestyle="--", lw=2, alpha=0.5)
    ax.add_patch(circle)
    ax.text(qx + 0.02, qy - 0.08, "Top-K Nearest Neighbors\n(Cosine Sim > 0.90)", fontsize=7.5, fontweight="bold", color=AMBER_ORANGE)

    ax.legend(loc="upper left", fontsize=7.5, frameon=True, facecolor="#FFFFFF")
    ax.text(0.5, 0.04, "Kid Intuition: Instead of matching exact words like 'cat', meaning-magnets find 'kitten' and 'feline' right next door!",
            ha="center", fontsize=8.5, fontweight="bold", color=OXFORD_NAVY, style="italic")

    ax.set_xlim(0.05, 0.95)
    ax.set_ylim(0, 0.9)
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(ASSETS_DIR / "fig_06_rag_vector_search.png", bbox_inches="tight")
    plt.close()


def fig_07_vllm_paged_attention():
    """Diagram 7: vLLM PagedAttention Virtual Memory Manager vs Wasteful Memory."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.2), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")

    # Left: Naive Contiguous Allocation (Wasteful)
    ax1.set_facecolor("#FDF7F7")
    ax1.set_title("Traditional Serving: Contiguous KV-Cache (60-80% Wasted)", fontsize=10, fontweight="bold", color=CORAL_RED, pad=10)
    ax1.text(0.5, 0.88, "Pre-allocates max tokens (e.g. 4096) for EVERY request.\nMassive internal memory fragmentation!",
             ha="center", fontsize=7.5, color=SLATE_DARK, transform=ax1.transAxes)

    rect1 = patches.Rectangle((0.15, 0.5), 0.25, 0.22, facecolor="#D4EFDF", edgecolor=EMERALD_GREEN, lw=1.5)
    ax1.add_patch(rect1)
    ax1.text(0.275, 0.61, "Tokens Used\n(25%)", ha="center", va="center", fontsize=7.5, color=OXFORD_NAVY)

    rect2 = patches.Rectangle((0.40, 0.5), 0.45, 0.22, facecolor="#FADBD8", edgecolor=CORAL_RED, lw=1.5, hatch="//")
    ax1.add_patch(rect2)
    ax1.text(0.625, 0.61, "WASTED RESERVED MEMORY\n(75% Locked & Unusable!)", ha="center", va="center", fontsize=7.5, fontweight="bold", color=CRIMSON)

    ax1.text(0.5, 0.25, "Result: GPU Runs Out Of Memory (OOM) after only 8 concurrent users!", ha="center", fontsize=8, color=CRIMSON, style="italic")
    ax1.axis("off")

    # Right: PagedAttention
    ax2.set_facecolor("#F4FAF6")
    ax2.set_title("vLLM PagedAttention: Dynamic Virtual Pages (<4% Waste)", fontsize=10, fontweight="bold", color=EMERALD_GREEN, pad=10)
    ax2.text(0.5, 0.88, "Allocates small 16-token non-contiguous physical pages,\nmapped via a virtual lookup table like an OS!",
             ha="center", fontsize=7.5, color=SLATE_DARK, transform=ax2.transAxes)

    for i in range(6):
        rx = 0.12 + (i % 3) * 0.28
        ry = 0.55 if i < 3 else 0.32
        rect = patches.FancyBboxPatch((rx, ry), 0.22, 0.18,
                                     boxstyle="round,pad=0.01,rounding_size=0.02",
                                     facecolor="#D4EFDF", edgecolor=EMERALD_GREEN, lw=1.5)
        ax2.add_patch(rect)
        ax2.text(rx + 0.11, ry + 0.09, f"Page {i+1}\n[16 Tokens]", ha="center", va="center", fontsize=7.5, fontweight="bold", color=OXFORD_NAVY)

    ax2.text(0.5, 0.12, "Result: 4x-10x Higher Serving Throughput with zero OOM crashes!", ha="center", fontsize=8, color=EMERALD_GREEN, fontweight="bold")
    ax2.axis("off")

    plt.tight_layout()
    plt.savefig(ASSETS_DIR / "fig_07_vllm_paged_attention.png", bbox_inches="tight")
    plt.close()


def fig_08_llm_security_fortress():
    """Diagram 8: The 4-Layer LLM Prompt Security Fortress."""
    fig, ax = plt.subplots(figsize=(9.5, 4.2), dpi=300)
    ax.set_facecolor("#FFFFFF")
    ax.set_title("The 4-Layer AppSec Fortress: Defense-in-Depth for LLM Systems", fontsize=11, fontweight="bold", color=OXFORD_NAVY, pad=12)

    layers = [
        ("Layer 1: Heuristic Firewall", "Inspects raw input for DAN\nexploits & instruction\noverrides before prompt.", "#FDEDEC", CORAL_RED),
        ("Layer 2: XML Delimiters", "Wraps untrusted input in\n<user_input> tags;\nsanitizes fake closure tags.", "#FEF9E7", AMBER_ORANGE),
        ("Layer 3: Canary Token", "Injects random GUID token\nin system directives.\nAudits model output.", "#EBF5FB", ROYAL_BLUE),
        ("Layer 4: Outbound DLP", "Scans model output for\nSSNs, API keys & credit cards;\nmasks before client view.", "#E8F8F5", EMERALD_GREEN),
    ]

    for i, (title, desc, bg, border) in enumerate(layers):
        x = 0.04 + i * 0.24
        rect = patches.FancyBboxPatch((x, 0.22), 0.21, 0.60,
                                     boxstyle="round,pad=0.02,rounding_size=0.03",
                                     facecolor=bg, edgecolor=border, linewidth=2)
        ax.add_patch(rect)
        ax.text(x + 0.105, 0.72, title, ha="center", va="center", fontsize=8, fontweight="bold", color=border)
        ax.text(x + 0.105, 0.44, desc, ha="center", va="center", fontsize=7.5, color=SLATE_DARK)

        if i < 3:
            ax.annotate("", xy=(x + 0.21 + 0.03, 0.52), xytext=(x + 0.21, 0.52),
                        arrowprops=dict(arrowstyle="->", color=OXFORD_NAVY, lw=2))

    ax.text(0.5, 0.06, "Kid Intuition: Like a castle with a moat, a gatekeeper, a secret dye-pack, and a disguise detector!",
            ha="center", fontsize=8.5, fontweight="bold", color=CRIMSON, style="italic")

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 0.9)
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(ASSETS_DIR / "fig_08_llm_security_fortress.png", bbox_inches="tight")
    plt.close()


def fig_09_concurrency_kitchen():
    """Diagram 9: Concurrency: Kitchen Chef (Asyncio) vs Royal Mic (GIL) vs Clone Army (Processes)."""
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(11, 4.2), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")

    # Chef (Asyncio)
    ax1.set_facecolor("#F4FAF6")
    ax1.set_title("1. Asyncio: The Master Chef", fontsize=9.5, fontweight="bold", color=EMERALD_GREEN)
    ax1.text(0.5, 0.85, "Single thread, non-blocking I/O.\nWhile soup simmers, chef chops onions.\nNever sits idle waiting for network!",
             ha="center", fontsize=7.5, color=SLATE_DARK, transform=ax1.transAxes)
    ax1.text(0.5, 0.45, "SOUP SIMMERING (I/O)\n▼\nSWITCH TO VEGGIES\n▼\nOVEN TIMER RINGS (Resume)",
             ha="center", va="center", fontsize=7.5, fontweight="bold", color=OXFORD_NAVY, bbox=dict(boxstyle="round", facecolor="#D4EFDF", edgecolor=EMERALD_GREEN))
    ax1.text(0.5, 0.12, "Best for: 10,000 Web Requests", ha="center", fontsize=8, fontweight="bold", color=EMERALD_GREEN)
    ax1.axis("off")

    # Royal Mic (GIL)
    ax2.set_facecolor("#FDF7F7")
    ax2.set_title("2. Threading: The Royal Mic (GIL)", fontsize=9.5, fontweight="bold", color=CORAL_RED)
    ax2.text(0.5, 0.85, "Multiple OS threads share memory,\nbut CPython GIL allows only ONE thread\nto hold the microphone at any microsecond!",
             ha="center", fontsize=7.5, color=SLATE_DARK, transform=ax2.transAxes)
    ax2.text(0.5, 0.45, "Thread A (Talking)\n[HOLDS GIL MIC]\n──────────────\nThread B (Waiting)\n[BLOCKED FROM CPU]",
             ha="center", va="center", fontsize=7.5, fontweight="bold", color=CRIMSON, bbox=dict(boxstyle="round", facecolor="#FADBD8", edgecolor=CORAL_RED))
    ax2.text(0.5, 0.12, "Best for: Disk / Network Wait", ha="center", fontsize=8, fontweight="bold", color=CORAL_RED)
    ax2.axis("off")

    # Multiprocessing
    ax3.set_facecolor("#EBF5FB")
    ax3.set_title("3. Multi-Process: Clone Army", fontsize=9.5, fontweight="bold", color=ROYAL_BLUE)
    ax3.text(0.5, 0.85, "Spawns separate Python processes,\neach with its own memory & GIL.\nRuns on 100% of CPU cores!",
             ha="center", fontsize=7.5, color=SLATE_DARK, transform=ax3.transAxes)
    ax3.text(0.5, 0.45, "Process 1 (Core 1) [Own GIL]\nProcess 2 (Core 2) [Own GIL]\nProcess 3 (Core 3) [Own GIL]\nProcess 4 (Core 4) [Own GIL]",
             ha="center", va="center", fontsize=7.5, fontweight="bold", color=OXFORD_NAVY, bbox=dict(boxstyle="round", facecolor="#EBF5FB", edgecolor=ROYAL_BLUE))
    ax3.text(0.5, 0.12, "Best for: Heavy Number Crunching", ha="center", fontsize=8, fontweight="bold", color=ROYAL_BLUE)
    ax3.axis("off")

    plt.tight_layout()
    plt.savefig(ASSETS_DIR / "fig_09_concurrency_kitchen.png", bbox_inches="tight")
    plt.close()


def fig_10_polyglot_rosetta_matrix():
    """Diagram 10: Polyglot Memory Footprint: Python Standard vs Slots vs PHP vs Node."""
    fig, ax = plt.subplots(figsize=(8.5, 4.2), dpi=300)
    ax.set_facecolor("#FAFAFA")
    ax.set_title("Domain Entity Memory Footprint: Python vs Node.js vs PHP 8.x", fontsize=11, fontweight="bold", color=OXFORD_NAVY, pad=12)

    categories = [
        "Python\nStandard Class\n(dict overhead)",
        "PHP 8.x\nzend_object\n(Zend Hashtable)",
        "Node.js\nV8 JSObject\n(Hidden Class)",
        "Python with\n__slots__ / Dataclass\n(Optimized C-struct)"
    ]
    bytes_used = [240, 128, 64, 48]
    colors = [CORAL_RED, AMBER_ORANGE, ROYAL_BLUE, EMERALD_GREEN]

    bars = ax.bar(categories, bytes_used, color=colors, width=0.55, edgecolor=OXFORD_NAVY, lw=1.2)

    for bar, val in zip(bars, bytes_used):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height + 6, f"{val} Bytes",
                ha="center", va="bottom", fontsize=9, fontweight="bold", color=OXFORD_NAVY)

    ax.set_ylabel("Memory per Instance (Bytes)", fontsize=9, fontweight="bold", color=OXFORD_NAVY)
    ax.set_ylim(0, 290)
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    ax.annotate("75% Memory Reduction!\nMatches & Beats V8 C++ Engine", xy=(3, 52), xytext=(2.2, 180),
                arrowprops=dict(arrowstyle="->", color=EMERALD_GREEN, lw=2),
                fontsize=8.5, fontweight="bold", color=EMERALD_GREEN,
                bbox=dict(boxstyle="round", facecolor="#D4EFDF", edgecolor=EMERALD_GREEN))

    plt.tight_layout()
    plt.savefig(ASSETS_DIR / "fig_10_polyglot_rosetta_matrix.png", bbox_inches="tight")
    plt.close()


if __name__ == "__main__":
    print("Generating Oxford Ebook High-DPI Visual Diagrams...")
    fig_01_deque_vs_list()
    fig_02_heap_tree_vs_array()
    fig_03_oop_metaclass_lifecycle()
    fig_04_numpy_strides_simd()
    fig_05_clean_architecture_onion()
    fig_06_rag_vector_search()
    fig_07_vllm_paged_attention()
    fig_08_llm_security_fortress()
    fig_09_concurrency_kitchen()
    fig_10_polyglot_rosetta_matrix()
    print("All 10 diagrams successfully generated in book_assets/!")
