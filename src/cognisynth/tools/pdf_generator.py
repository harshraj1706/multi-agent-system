"""
PDF Generator for CogniSynth Research Reports.
Converts Markdown intelligence reports into styled, publication-grade executive PDFs.
"""

import io
import re
from datetime import datetime, timezone
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    HRFlowable,
    Table,
    TableStyle,
    KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Adds running headers and 'Page X of Y' footers to every page."""

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

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        # Running Header (pages 2+)
        if self._pageNumber > 1:
            self.drawString(54, 750, "CogniSynth | Autonomous Decision Intelligence Platform")
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.5)
            self.line(54, 744, 558, 744)

        # Running Footer
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(54, 45, 558, 45)
        self.drawString(54, 32, f"Confidential Intelligence Report — Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
        self.drawRightString(558, 32, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


def markdown_to_pdf(
    title: str,
    markdown_content: str,
    confidence_score: float = 0.85,
    sources_count: int = 4,
    claims_count: int = 10,
) -> bytes:
    """
    Render markdown report into a publication-ready PDF byte stream.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    style_title = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=12,
    )
    style_h1 = ParagraphStyle(
        "ReportH1",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True,
    )
    style_h2 = ParagraphStyle(
        "ReportH2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#334155"),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )
    style_body = ParagraphStyle(
        "ReportBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#1E293B"),
        spaceAfter=6,
    )
    style_bullet = ParagraphStyle(
        "ReportBullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
        leftIndent=15,
        spaceAfter=4,
    )

    story = []

    # Title & Branding Banner
    clean_title = re.sub(r"^#+\s*", "", title).strip()
    story.append(Paragraph(clean_title, style_title))

    # Metadata Badges Table
    conf_pct = f"{int(confidence_score * 100)}%"
    meta_data = [
        [
            Paragraph("<b>Platform:</b> CogniSynth Swarm", style_body),
            Paragraph(f"<b>Derived Confidence:</b> {conf_pct}", style_body),
            Paragraph(f"<b>Sources Audited:</b> {sources_count}", style_body),
            Paragraph(f"<b>Claims Grounded:</b> {claims_count}", style_body),
        ]
    ]
    meta_table = Table(meta_data, colWidths=[126, 126, 126, 126])
    meta_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ])
    )
    story.append(meta_table)
    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#7C3AED"), spaceAfter=14))

    # Parse and add Markdown elements
    lines = markdown_content.split("\n")
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            story.append(Spacer(1, 4))
            continue

        # Skip main title if repeated
        if line.startswith("# ") and clean_title.lower() in line.lower():
            continue

        # Clean markdown bold/italic tags for ReportLab paragraphs
        formatted = line
        formatted = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", formatted)
        formatted = re.sub(r"\*(.+?)\*", r"<i>\1</i>", formatted)
        formatted = re.sub(r"`(.+?)`", r"<font face='Courier'>\1</font>", formatted)
        # Convert links [text](url) into clean clickable links
        formatted = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"<a href='\2' color='#4F46E5'><u>\1</u></a>", formatted)

        # Headings
        if line.startswith("### "):
            story.append(Paragraph(formatted[4:], style_h2))
        elif line.startswith("## "):
            story.append(Spacer(1, 6))
            story.append(Paragraph(formatted[3:], style_h1))
        elif line.startswith("# "):
            story.append(Spacer(1, 8))
            story.append(Paragraph(formatted[2:], style_h1))
        # Bullet list
        elif line.startswith("- ") or line.startswith("* ") or re.match(r"^\d+\.\s", line):
            bullet_text = re.sub(r"^[-*]\s+|\d+\.\s+", "", formatted)
            story.append(Paragraph(f"• {bullet_text}", style_bullet))
        # Horizontal Rule
        elif line.startswith("---") or line.startswith("***"):
            story.append(Spacer(1, 6))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E2E8F0"), spaceAfter=8))
        # Normal paragraph
        else:
            # Escape raw unclosed HTML chars
            safe_text = formatted.replace("< ", "&lt; ").replace(" >", " &gt;")
            try:
                story.append(Paragraph(safe_text, style_body))
            except Exception:
                story.append(Paragraph(re.sub(r"<[^>]+>", "", safe_text), style_body))

    doc.build(story, canvasmaker=NumberedCanvas)
    return buffer.getvalue()
