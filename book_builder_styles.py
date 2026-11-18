"""
The Oxford Enterprise Python Compendium: Publication Styles & Layout Engine
============================================================================
Defines publication-grade typography, Oxford color schemes, custom callout
containers, code block formatters, and two-pass running header/footer canvas.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Union

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    Flowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

# ==============================================================================
# 1. Oxford Publication Color Palette
# ==============================================================================
OXFORD_NAVY = colors.HexColor("#002147")     # Primary Heading & Oxford Branding
OXFORD_BLUE = colors.HexColor("#0B3C5D")     # Secondary Highlights
OXFORD_GOLD = colors.HexColor("#D4AF37")     # Accents, Awards, Special Borders
OXFORD_CRIMSON = colors.HexColor("#8A1538")  # Warnings, Important Rules, Critical Pitfalls
CHARCOAL_TEXT = colors.HexColor("#1A202C")   # Body text (crisp, high readability)
SLATE_MUTED = colors.HexColor("#4A5568")     # Subtitles, captions, footers
BG_CREAM = colors.HexColor("#FCFDFD")        # Soft page background
BG_CODE = colors.HexColor("#F8F9FA")         # Code block background
BORDER_CODE = colors.HexColor("#CBD5E0")     # Code block outline
BG_INTUITION = colors.HexColor("#F0FFF4")    # Light Mint for Age-10+ Intuition boxes
BORDER_INTUITION = colors.HexColor("#27AE60")# Emerald Green
BG_ARCHITECT = colors.HexColor("#F7FAFC")    # Light Lavender/Grey for Architect Deep Dives
BORDER_ARCHITECT = colors.HexColor("#4A5568")# Slate
BG_CHEAT = colors.HexColor("#FFFDF0")        # Light Gold for Cheats & Tricks
BORDER_CHEAT = colors.HexColor("#D4AF37")    # Gold border
DIVIDER_LINE = colors.HexColor("#E2E8F0")

USABLE_WIDTH = 522  # 612 (letter width) - 2 * 45 (margins)


# ==============================================================================
# 2. Typography Styles
# ==============================================================================
def get_oxford_styles():
    base = getSampleStyleSheet()

    styles = {
        "Normal": base["Normal"],
        "CoverTitle": ParagraphStyle(
            "CoverTitle",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=28,
            leading=34,
            textColor=OXFORD_NAVY,
            alignment=1,  # Center
            spaceAfter=12,
        ),
        "CoverSubtitle": ParagraphStyle(
            "CoverSubtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=13,
            leading=18,
            textColor=SLATE_MUTED,
            alignment=1,
            spaceAfter=20,
        ),
        "CoverBadge": ParagraphStyle(
            "CoverBadge",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=14,
            textColor=OXFORD_GOLD,
            alignment=1,
            spaceAfter=15,
        ),
        "PartBanner": ParagraphStyle(
            "PartBanner",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=colors.white,
            alignment=1,
        ),
        "ChapterNumber": ParagraphStyle(
            "ChapterNumber",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=15,
            textColor=OXFORD_GOLD,
            textTransform="uppercase",
            spaceAfter=4,
        ),
        "ChapterTitle": ParagraphStyle(
            "ChapterTitle",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=21,
            leading=25,
            textColor=OXFORD_NAVY,
            spaceAfter=12,
            keepWithNext=True,
        ),
        "SectionHeading": ParagraphStyle(
            "SectionHeading",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=OXFORD_BLUE,
            spaceBefore=12,
            spaceAfter=6,
            keepWithNext=True,
        ),
        "SubsectionHeading": ParagraphStyle(
            "SubsectionHeading",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=15,
            textColor=OXFORD_CRIMSON,
            spaceBefore=8,
            spaceAfter=4,
            keepWithNext=True,
        ),
        "Body": ParagraphStyle(
            "Body",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=14,
            textColor=CHARCOAL_TEXT,
            spaceAfter=7,
        ),
        "BodyBold": ParagraphStyle(
            "BodyBold",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=14,
            textColor=CHARCOAL_TEXT,
            spaceAfter=7,
        ),
        "AnalogyBody": ParagraphStyle(
            "AnalogyBody",
            parent=base["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor("#1C3D2B"),
            spaceAfter=4,
        ),
        "BoxHeader": ParagraphStyle(
            "BoxHeader",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=14,
            textColor=OXFORD_NAVY,
            spaceAfter=4,
        ),
        "CodeText": ParagraphStyle(
            "CodeText",
            parent=base["Normal"],
            fontName="Courier",
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#2D3748"),
        ),
        "Caption": ParagraphStyle(
            "Caption",
            parent=base["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=8,
            leading=11,
            textColor=SLATE_MUTED,
            alignment=1,  # Center
            spaceBefore=4,
            spaceAfter=8,
        ),
        "TableHeader": ParagraphStyle(
            "TableHeader",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=colors.white,
            alignment=1,
        ),
        "TableCell": ParagraphStyle(
            "TableCell",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=CHARCOAL_TEXT,
        ),
        "TableCellBold": ParagraphStyle(
            "TableCellBold",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=11,
            textColor=OXFORD_NAVY,
        ),
        "TOCLine": ParagraphStyle(
            "TOCLine",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=15,
            textColor=CHARCOAL_TEXT,
        ),
    }
    return styles


# ==============================================================================
# 3. Two-Pass Running Header & Footer Canvas
# ==============================================================================
class OxfordNumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas recording total page count to render:
    - Running Oxford header line with publication imprint
    - Running footer with dynamic 'Page X of Y' pagination
    - Automatically suppresses headers and footers on Cover and Imprint pages.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages: int):
        # Page 1 is Cover; Page 2 is Imprint / Title info
        if self._pageNumber > 2:
            self.saveState()
            
            # Running Header (Top)
            self.setStrokeColor(colors.HexColor("#002147"))
            self.setLineWidth(0.75)
            self.line(45, 750, 612 - 45, 750)

            self.setFont("Helvetica-Bold", 7.5)
            self.setFillColor(colors.HexColor("#002147"))
            self.drawString(45, 755, "THE OXFORD ENTERPRISE PYTHON COMPENDIUM")

            self.setFont("Helvetica", 7.5)
            self.setFillColor(colors.HexColor("#718096"))
            self.drawRightString(612 - 45, 755, "Oxford Academic & DeepMind Research Guild")

            # Running Footer (Bottom)
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.5)
            self.line(45, 45, 612 - 45, 45)

            self.setFont("Helvetica", 7.5)
            self.setFillColor(colors.HexColor("#718096"))
            self.drawString(45, 33, "Definitive Edition • For Ages 10 to Staff Software Architects")

            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#002147"))
            page_text = f"Page {self._pageNumber} of {total_pages}"
            self.drawRightString(612 - 45, 33, page_text)

            self.restoreState()


# ==============================================================================
# 4. Custom Flowable Container Builders
# ==============================================================================
def make_callout_box(
    title: str,
    paragraphs: List[Paragraph],
    bg_color=BG_ARCHITECT,
    border_color=BORDER_ARCHITECT,
    title_color=OXFORD_NAVY,
    icon: str = "💡",
) -> Table:
    """Build a styled, full-width callout container with an accent left border."""
    styles = get_oxford_styles()
    title_p = Paragraph(f"<b>{icon} {title}</b>", ParagraphStyle(
        "CalloutH", parent=styles["BoxHeader"], textColor=title_color, fontSize=9.5, leading=13
    ))

    content = [title_p, Spacer(1, 3)] + paragraphs
    table = Table([[content]], colWidths=[USABLE_WIDTH])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg_color),
        ("LINEBEFORE", (0, 0), (0, -1), 3.5, border_color),
        ("BOX", (0, 0), (-1, -1), 0.5, border_color),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    return table


def make_intuition_box(concept_name: str, analogy_text: str, why_it_matters: str) -> Table:
    """Specialized callout for Age-10+ Intuitive Analogy."""
    styles = get_oxford_styles()
    p1 = Paragraph(f"<b>The Real-World Picture:</b> {analogy_text}", styles["AnalogyBody"])
    p2 = Paragraph(f"<b>Why Grown-Up Architects Care:</b> {why_it_matters}", styles["Body"])
    return make_callout_box(
        f"Intuition for Young Thinkers (Age 10+): {concept_name}",
        [p1, Spacer(1, 2), p2],
        bg_color=BG_INTUITION,
        border_color=BORDER_INTUITION,
        title_color=colors.HexColor("#1E5631"),
        icon="🌱",
    )


def make_cheat_box(title: str, cheat_items: List[str]) -> Table:
    """Cheats & Tricks quick-reference card."""
    styles = get_oxford_styles()
    paras = []
    for item in cheat_items:
        paras.append(Paragraph(f"• {item}", styles["Body"]))
    return make_callout_box(
        f"Cheats & Tricks: {title}",
        paras,
        bg_color=BG_CHEAT,
        border_color=BORDER_CHEAT,
        title_color=colors.HexColor("#8A6D3B"),
        icon="⚡",
    )


def make_code_box(code_text: str, caption: str = "Production Implementation") -> Table:
    """Formatted code snippet block with syntax container."""
    styles = get_oxford_styles()
    header_p = Paragraph(f"<b>Python 3.14 Implementation: {caption}</b>", ParagraphStyle(
        "CodeH", fontName="Helvetica-Bold", fontSize=8, leading=11, textColor=OXFORD_BLUE
    ))

    # Clean code lines to avoid XML tag issues
    safe_code = code_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    lines = safe_code.strip().split("\n")
    code_paras = [Paragraph(line.replace(" ", "&nbsp;"), styles["CodeText"]) for line in lines]

    content = [header_p, Spacer(1, 3)] + code_paras
    table = Table([[content]], colWidths=[USABLE_WIDTH])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BG_CODE),
        ("BOX", (0, 0), (-1, -1), 0.75, BORDER_CODE),
        ("LINEBEFORE", (0, 0), (0, -1), 3, OXFORD_NAVY),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return table


def make_standard_table(
    headers: List[str], rows: List[List[str]], col_widths: List[float] = None
) -> Table:
    """Create publication-standard styled table with Oxford Navy header and alternating row shading."""
    styles = get_oxford_styles()

    header_cells = [Paragraph(h, styles["TableHeader"]) for h in headers]
    data_cells = [header_cells]

    for r_idx, row in enumerate(rows):
        row_cells = []
        for c_idx, cell in enumerate(row):
            is_bold = (c_idx == 0)
            st = styles["TableCellBold"] if is_bold else styles["TableCell"]
            row_cells.append(Paragraph(cell, st))
        data_cells.append(row_cells)

    if not col_widths:
        w = USABLE_WIDTH / len(headers)
        col_widths = [w] * len(headers)

    t = Table(data_cells, colWidths=col_widths, repeatRows=1)
    t_style = [
        ("BACKGROUND", (0, 0), (-1, 0), OXFORD_NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
    ]

    for i in range(1, len(data_cells)):
        if i % 2 == 0:
            t_style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#F8F9FA")))
        else:
            t_style.append(("BACKGROUND", (0, i), (-1, i), colors.white))

    t.setStyle(TableStyle(t_style))
    return t


def make_figure_block(image_path: str, caption_text: str, width: float = 480, height: float = 220) -> List[Flowable]:
    """Return an image with a centered caption block."""
    styles = get_oxford_styles()
    if not os.path.exists(image_path):
        return [Paragraph(f"[Image not found: {image_path}]", styles["Body"])]
    img = Image(image_path, width=width, height=height)
    caption = Paragraph(f"<b>Figure:</b> {caption_text}", styles["Caption"])
    return [img, caption]
