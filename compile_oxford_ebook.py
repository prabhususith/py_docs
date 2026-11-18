"""
The Oxford Enterprise Python Compendium: Master Compilation Engine
===================================================================
Coordinates the multi-stage assembly of Front Matter, Foundations, Roles,
Advanced Systems, Diagrams, Cheatsheets, Glossary, and Diploma into the
definitive publication-quality PDF Ebook.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate

from book_builder_styles import OxfordNumberedCanvas
from book_builder_chapters_foundations import build_front_matter, build_part_1_foundations
from book_builder_chapters_roles import build_part_2_roles
from book_builder_chapters_systems import build_part_3_and_back_matter

# Output Path
OUTPUT_PDF = Path("The_Oxford_Enterprise_Python_Compendium.pdf")


def compile_ebook():
    start_time = time.time()
    print("================================================================================")
    print(" OXFORD ENTERPRISE PYTHON COMPENDIUM: MULTI-AGENT PUBLICATION COMPILER")
    print("================================================================================")
    print("Phase 1: Validating high-DPI visual assets...")
    required_figures = [
        "book_assets/fig_01_deque_vs_list.png",
        "book_assets/fig_02_heap_tree_vs_array.png",
        "book_assets/fig_03_oop_metaclass_lifecycle.png",
        "book_assets/fig_04_numpy_strides_simd.png",
        "book_assets/fig_05_clean_architecture_onion.png",
        "book_assets/fig_06_rag_vector_search.png",
        "book_assets/fig_07_vllm_paged_attention.png",
        "book_assets/fig_08_llm_security_fortress.png",
        "book_assets/fig_09_concurrency_kitchen.png",
        "book_assets/fig_10_polyglot_rosetta_matrix.png",
    ]
    for fig in required_figures:
        if not os.path.exists(fig):
            raise FileNotFoundError(f"Missing required publication figure: {fig}")
    print(f"  [PASS] All {len(required_figures)} visual figures verified on disk.")

    print("\nPhase 2: Assembling modular book flowables across all agents...")
    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=letter,
        leftMargin=45,
        rightMargin=45,
        topMargin=54,
        bottomMargin=54,
        title="The Oxford Illustrated Compendium of Enterprise Python & Systems Architecture",
        author="Oxford AI & Systems Guild & DeepMind Research Guild",
        subject="Enterprise Python, Computer Science Foundations, AI/ML, and Polyglot Architecture",
        keywords="Python, DSA, OOP, Metaclasses, FastAPI, AI, RAG, MLOps, AppSec, Polyglot",
    )

    story = []

    # 1. Front Matter: Cover, Imprint, TOC, Preface
    print("  • Compiling Front Matter (Cover, Imprint, Table of Contents, Preface)...")
    front_story = build_front_matter()
    story.extend(front_story)

    # 2. Part I: Foundations (DSA, OOP, Data Science Core)
    print("  • Compiling Part I: The Three Foundational Pillars (Chapters 1-3)...")
    foundations_story = build_part_1_foundations()
    story.extend(foundations_story)

    # 3. Part II: The Seven Roles (Full-Stack, AI/ML, MLOps, Data Sci, Data Eng, AppSec, Polyglot)
    print("  • Compiling Part II: The Seven Enterprise Roles (Chapters 4-10)...")
    roles_story = build_part_2_roles()
    story.extend(roles_story)

    # 4. Part III: Advanced Systems & Back Matter
    print("  • Compiling Part III & Back Matter (Concurrency, GUI, Glossary, Diploma)...")
    systems_story = build_part_3_and_back_matter()
    story.extend(systems_story)

    total_flowables = len(story)
    print(f"  [PASS] Successfully assembled {total_flowables} flowable elements.")

    print("\nPhase 3: Executing two-pass compilation with OxfordNumberedCanvas...")
    doc.build(story, canvasmaker=OxfordNumberedCanvas)

    elapsed = time.time() - start_time
    file_size_kb = OUTPUT_PDF.stat().st_size / 1024.0

    print("\n================================================================================")
    print(" [PUBLICATION SUCCESS] EBOOK GENERATION COMPLETE")
    print("================================================================================")
    print(f"  • Destination File : {OUTPUT_PDF.resolve()}")
    print(f"  • File Size        : {file_size_kb:,.2f} KB ({file_size_kb/1024.0:.2f} MB)")
    print(f"  • Build Duration   : {elapsed:.2f} seconds")
    print(f"  • Status           : Publication-Ready PDF (Ages 10 to Staff Software Architects)")
    print("================================================================================")


if __name__ == "__main__":
    compile_ebook()
