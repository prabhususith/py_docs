"""
The Oxford Enterprise Python Compendium: Systems Engineering & Back Matter
===========================================================================
Constructs Chapters 11 and 12 (Concurrency, GIL, Desktop Visual Apps) and
the Back Matter (Master Glossary, Author Epilogue, and Oxford Scholar Diploma).
"""

from __future__ import annotations

from typing import List
from reportlab.platypus import Flowable, PageBreak, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
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


def build_part_3_and_back_matter() -> List[Flowable]:
    """Generate Chapters 11 & 12, Glossary, Epilogue, and Certificate."""
    styles = get_oxford_styles()
    story: List[Flowable] = []

    # ==========================================================================
    # CHAPTER 11: HIGH-PERFORMANCE CONCURRENCY & THE GIL MYSTERY
    # ==========================================================================
    story.append(Paragraph("PART III: ADVANCED SYSTEMS & DESKTOP VISUAL ENGINEERING", styles["ChapterNumber"]))
    story.append(Paragraph("Chapter 11: High-Performance Concurrency, Asyncio & The GIL Mystery", styles["ChapterTitle"]))
    story.append(Paragraph("The Master Kitchen Chef, The Royal Microphone, and The Kitchen Clones", styles["Caption"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "Concurrency is often viewed as the most perilous topic in computer systems. Race conditions, deadlocks, and "
        "mysterious thread crashes haunt developers. But when broken down into physical models, Python's three concurrency "
        "engines—Asyncio, Threading, and Multiprocessing—become delightfully clear.",
        styles["Body"]
    ))

    # Analogy 11: Concurrency Kitchen
    story.append(make_intuition_box(
        "The Master Kitchen Chef, The Royal Microphone, and The Kitchen Clones",
        "Imagine three different ways to run a busy gourmet restaurant:<br/>"
        "1. <b>Asyncio (The Master Chef):</b> One single, brilliant chef. While pasta water is boiling (waiting for network I/O), "
        "the chef does not stand still staring at the pot! They chop carrots. When the oven timer dings, they flip the fish. "
        "Zero waiting, single thread, handles 10,000 orders effortlessly!<br/>"
        "2. <b>Threading (The Royal Microphone / The GIL):</b> Multiple cooks share the exact same kitchen counter and pantry (shared RAM). "
        "However, there is only ONE golden royal microphone! Only the cook holding the microphone is allowed to speak to the stove. "
        "Great if cooks spend most of their time waiting for deliveries (network I/O), but if all cooks want to chop onions (CPU work), "
        "they bump into each other fighting for the microphone.<br/>"
        "3. <b>Multiprocessing (The Kitchen Clones):</b> You build four completely separate kitchens in four separate buildings! "
        "Each kitchen has its own chef, its own pantry, and its own microphone. Zero fighting, 100% CPU core utilization!",
        "CPython's Global Interpreter Lock (GIL) protects memory reference counting. In modern Python 3.14+ (PEP 703), free-threaded "
        "Python is unlocking true multi-core threading without the GIL, revolutionizing AI and high-frequency computation."
    ))

    story.append(Spacer(1, 10))
    story.extend(make_figure_block(
        "book_assets/fig_09_concurrency_kitchen.png",
        "The Concurrency Spectrum: 1) Asyncio (The Master Chef), 2) Threading (The Royal GIL Mic), 3) Multiprocessing (The Kitchen Clones).",
        width=470, height=210
    ))
    story.append(Spacer(1, 10))

    # Code Box: Concurrency Options
    code_conc = (
        "import asyncio\n"
        "from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor\n\n"
        "# 1. Asyncio: Structured Concurrency via TaskGroups (Python 3.11+)\n"
        "async def handle_io_requests():\n"
        "    async with asyncio.TaskGroup() as tg:\n"
        "        task1 = tg.create_task(fetch_user_data(user_id=1))\n"
        "        task2 = tg.create_task(fetch_billing_data(user_id=1))\n"
        "    # If either task fails, the other is automatically and cleanly cancelled!\n"
        "    return task1.result(), task2.result()\n\n"
        "# 2. CPU-Bound Heavy Math: ProcessPoolExecutor (Bypasses GIL!)\n"
        "def compute_heavy_crypto_hash(data: bytes) -> str:\n"
        "    return hashlib.sha256(data).hexdigest()\n\n"
        "with ProcessPoolExecutor(max_workers=8) as executor:\n"
        "    results = list(executor.map(compute_heavy_crypto_hash, data_chunks))"
    )
    story.append(make_code_box(code_conc, "Asyncio TaskGroup & ProcessPoolExecutor"))
    story.append(Spacer(1, 10))

    # Concurrency Matrix Cheat Sheet
    story.append(Paragraph("Concurrency Model Selection Matrix", styles["SubsectionHeading"]))
    conc_headers = ["Concurrency Model", "Execution Mechanism", "Best Workload", "CPython GIL Impact"]
    conc_rows = [
        ["asyncio (Event Loop)", "Single thread, cooperative multitasking", "High-volume web requests, APIs, WebSockets", "Completely unblocked by I/O waits"],
        ["Threading (threading)", "Multiple OS threads, shared memory", "File I/O, disk logging, background sync", "Serialized on CPU bytecode by GIL"],
        ["Multiprocessing", "Separate OS processes, isolated heaps", "Heavy matrix math, cryptography, video encoding", "Completely bypasses GIL (True multi-core)"],
        ["Free-Threaded (PEP 703)", "Multi-thread with biased reference counting", "Next-gen parallel AI & multi-core Python", "GIL removed; thread-safe lock-free memory"],
    ]
    story.append(make_standard_table(conc_headers, conc_rows, col_widths=[110, 140, 140, 132]))
    story.append(PageBreak())

    # ==========================================================================
    # CHAPTER 12: DESKTOP GUI & VISUAL DASHBOARDS
    # ==========================================================================
    story.append(Paragraph("Chapter 12: Desktop GUI & Visual Applications", styles["ChapterTitle"]))
    story.append(Paragraph("The Airplane Cockpit: CustomTkinter, Streamlit AI Playgrounds, and PyQt6 Threads", styles["Caption"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "Software should not live only in terminal logs and cloud servers. Visual dashboards and desktop interfaces give users "
        "intuitive, immediate control over complex algorithms, vector embeddings, and enterprise databases.",
        styles["Body"]
    ))

    # Analogy 12: Cockpit
    story.append(make_intuition_box(
        "The Jet Airplane Cockpit with Glowing Dials",
        "Imagine an airplane pilot flying at 35,000 feet. If the pilot had to type raw command-line commands to lower the landing gear "
        "or check fuel levels, flying would be terrifying! Instead, the cockpit has glowing dials, toggles, altitude meters, and alarms.<br/>"
        "A <b>GUI (Graphical User Interface)</b> is that cockpit for your software! Modern Python offers visual superpowers:<br/>"
        "• <b>Tkinter / CustomTkinter:</b> Lightweight desktop apps with sleek dark-mode sliders and zero bulky browser engines.<br/>"
        "• <b>Streamlit:</b> Instant reactive web applications for AI and data science with built-in charts and sliders.<br/>"
        "• <b>PyQt6:</b> Industrial-strength enterprise desktop software with multi-threaded background workers and Signals & Slots.",
        "A critical rule of GUI architecture: NEVER run heavy math or network calls on the GUI main thread! Doing so freezes the "
        "window ('Application Not Responding'). Always offload background tasks to worker threads (e.g. PyQt6 `QThread`) and communicate "
        "safely via signals."
    ))

    # Code Box: PyQt6 Non-Blocking Thread Worker
    code_gui = (
        "from PyQt6.QtCore import QThread, pyqtSignal\n"
        "from PyQt6.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget\n\n"
        "# 1. Worker Thread: Keeps GUI butter-smooth during heavy processing\n"
        "class HeavyComputeWorker(QThread):\n"
        "    progress_updated = pyqtSignal(int)   # Thread-safe dispatch\n"
        "    calculation_finished = pyqtSignal(str)\n\n"
        "    def run(self):\n"
        "        for i in range(1, 101):\n"
        "            self.msleep(20) # Simulated heavy computation\n"
        "            self.progress_updated.emit(i)\n"
        "        self.calculation_finished.emit('Calculation 100% Complete!')\n\n"
        "# 2. Main Window: Connects Signals & Slots safely\n"
        "class EnterpriseDashboard(QMainWindow):\n"
        "    def __init__(self):\n"
        "        super().__init__()\n"
        "        self.worker = HeavyComputeWorker()\n"
        "        self.worker.progress_updated.connect(self.update_progress_bar)"
    )
    story.append(make_code_box(code_gui, "PyQt6 Non-Blocking QThread & Signals/Slots"))
    story.append(Spacer(1, 10))

    # Desktop Framework Comparison Cheat Sheet
    story.append(Paragraph("Python Desktop & Visual Framework Comparison Matrix", styles["SubsectionHeading"]))
    gui_headers = ["Framework", "Target Platform", "Rendering Engine", "Best Production Use Case"]
    gui_rows = [
        ["Tkinter (Standard Lib)", "Desktop (Win/Mac/Linux)", "Native Tk window widgets", "Simple internal administrative utilities, zero extra pip dependencies"],
        ["CustomTkinter", "Modern Desktop", "Custom themed widgets", "Sleek dark-mode enterprise control panels, local AI dashboards"],
        ["Streamlit", "Reactive Web Browser", "React/Tornado web server", "Instant GenAI playgrounds, vector inspection, rapid executive prototypes"],
        ["PyQt6 / Qt6", "Enterprise Desktop", "C++ Qt6 native hardware engine", "High-frequency trading terminals, CAD software, complex multi-window apps"],
    ]
    story.append(make_standard_table(gui_headers, gui_rows, col_widths=[110, 115, 125, 172]))
    story.append(PageBreak())

    # ==========================================================================
    # BACK MATTER: MASTER GLOSSARY & EPILOGUE & DIPLOMA
    # ==========================================================================
    story.append(Paragraph("BACK MATTER: REFERENCE & CERTIFICATION", styles["ChapterNumber"]))
    story.append(Paragraph("The Young Scholar & Staff Architect Master Glossary", styles["ChapterTitle"]))
    story.append(Paragraph("An Essential A to Z Dictionary of Enterprise Computer Systems", styles["Caption"]))
    story.append(Spacer(1, 8))

    glossary_terms = [
        ("Amortized O(1)", "An operation that is usually instantaneous (O(1)), with rare, predictable reallocations that average out to constant time over many operations (like dynamic array appending)."),
        ("Asynchronous I/O (asyncio)", "A design pattern where a single execution thread pauses during network or disk wait states to execute other tasks, maximizing hardware efficiency."),
        ("Binary Min-Heap", "A complete binary tree where the parent node is always smaller than or equal to its children, allowing instant O(1) peek and O(log N) extraction of the minimum value."),
        ("Canary Token", "A unique cryptographic secret string planted in prompts or databases. If leaked in untrusted output, it acts like a bank dye-pack, instantly alerting security monitors."),
        ("Clean Architecture", "A software design philosophy where core business domain logic has zero dependencies on databases, web frameworks, or third-party libraries (Dependency Inversion)."),
        ("Continuous Batching", "An LLM inference serving optimization where new requests are injected into the neural network forward pass as soon as any previous sequence finishes, maximizing GPU utilization."),
        ("Data Descriptor", "A Python class attribute that implements `__get__` and `__set__`, acting as a gatekeeper to validate data, enforce typing, and control attribute access (PEP 487)."),
        ("Global Interpreter Lock (GIL)", "A mutex in CPython that prevents multiple native OS threads from executing Python bytecode simultaneously, ensuring thread-safe reference counting."),
        ("Idempotence", "A mathematical and software property where executing an operation multiple times produces the exact same result as executing it once (critical for data engineering pipelines)."),
        ("Low-Rank Adaptation (LoRA)", "A Parameter-Efficient Fine-Tuning (PEFT) method that freezes base model weights and trains tiny rank decomposition matrices, reducing trainable parameters to <0.1%."),
        ("PagedAttention", "A virtual memory management algorithm for LLMs (used in vLLM) that stores Key-Value cache tokens in non-contiguous physical pages, cutting memory waste from 75% to <4%."),
        ("Protocol (Structural Duck Typing)", "A PEP 544 Python typing construct where classes satisfy an interface simply by possessing the required methods, without explicitly inheriting from a base class."),
        ("Retrieval-Augmented Generation (RAG)", "An architecture that retrieves verified factual documents from a vector database before an LLM answers, neutralizing hallucinations."),
        ("SIMD (Single Instruction, Multiple Data)", "Hardware processor capability (AVX2/AVX-512) allowing a CPU to perform arithmetic on 4, 8, or 16 numbers simultaneously in a single clock cycle."),
        ("Vector Embedding", "A mathematical transformation converting text, images, or audio into an array of floating-point coordinates where geometric distance corresponds to semantic similarity."),
    ]

    glossary_rows = []
    for term, definition in glossary_terms:
        glossary_rows.append([
            Paragraph(f"<b>{term}</b>", styles["TableCellBold"]),
            Paragraph(definition, styles["TableCell"]),
        ])

    glossary_table = Table(glossary_rows, colWidths=[140, 382])
    glossary_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#EDF2F7")),
    ]))
    story.append(glossary_table)
    story.append(PageBreak())

    # Epilogue
    story.append(Paragraph("AUTHOR'S EPILOGUE", styles["ChapterNumber"]))
    story.append(Paragraph("Engineering with Joy, Rigor, and Endless Curiosity", styles["ChapterTitle"]))
    story.append(Spacer(1, 10))

    epilogue_text = (
        "We live in an extraordinary golden age of computation. Every day, artificial intelligence models grow more capable, "
        "data pipelines process unimaginable petabytes of information, and autonomous agents orchestrate complex real-world workflows.<br/><br/>"
        "Yet throughout all this technological acceleration, the most enduring truth remains unchanged: "
        "<b>Simplicity is the ultimate sophistication.</b><br/><br/>"
        "Whether you are ten years old writing your first loop to count stars, or a Principal Architect designing a distributed AI serving "
        "cluster for 50 million users, the joy of software engineering is fundamentally about building things that work with beauty, "
        "clarity, and grace.<br/><br/>"
        "Never stop taking things apart to see how they work. Never be satisfied with magic words you do not understand. "
        "Ask 'Why?'. Draw the cafeteria trays. Measure the conveyor belts. Guard the castle moats. And above all, share what you build "
        "with generosity and kindness.<br/><br/>"
        "<i>— The Oxford AI & Systems Guild</i>"
    )
    story.append(Paragraph(epilogue_text, styles["Body"]))
    story.append(Spacer(1, 30))

    # Certificate of Mastery
    cert_data = [
        [
            Paragraph(
                "<font size=14 color='#D4AF37'><b>★ OXFORD ACADEMIC PRESS & DEEPMIND RESEARCH GUILD ★</b></font><br/><br/>"
                "<font size=18 color='#002147'><b>MASTER COMPLETER DIPLOMA</b></font><br/>"
                "<font size=10 color='#4A5568'>IN ENTERPRISE PYTHON & SYSTEMS ARCHITECTURE</font><br/><br/>"
                "<font size=9.5 color='#1A202C'>"
                "This certifies that the inquisitive scholar has journeyed through the Three Grand Foundations,<br/>"
                "the Seven Enterprise Roles, High-Performance Concurrency, and Polyglot Systems Design,<br/>"
                "demonstrating mastery of physical intuition, algorithmic rigor, and defect-free code."
                "</font><br/><br/>"
                "<font size=8.5 color='#8A1538'><b>AWARDED WITH HIGHEST HONORS • OXFORD DEFECT-FREE STANDARD</b></font>",
                ParagraphStyle("CertText", parent=styles["Normal"], alignment=1, leading=16)
            )
        ]
    ]
    cert_table = Table(cert_data, colWidths=[USABLE_WIDTH])
    cert_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFFDF7")),
        ("BOX", (0, 0), (-1, -1), 3, OXFORD_GOLD),
        ("INNERGRID", (0, 0), (-1, -1), 1, OXFORD_NAVY),
        ("TOPPADDING", (0, 0), (-1, -1), 22),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 22),
        ("LEFTPADDING", (0, 0), (-1, -1), 25),
        ("RIGHTPADDING", (0, 0), (-1, -1), 25),
    ]))
    story.append(cert_table)

    return story
