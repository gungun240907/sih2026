"""Export resume analysis as markdown / txt / pdf."""

import io


def to_markdown(text: str, analysis: dict, source: str) -> str:
    lines = [
        f"# Resume Analysis — {source}",
        "",
        f"**ATS score:** {analysis.get('ats_score', 0)}/100",
        "",
        "## Summary",
        analysis.get("summary", ""),
        "",
        "## Skills",
        ", ".join(analysis.get("skills", [])) or "—",
        "",
        "## Suggested search",
        f"Keywords: {', '.join(analysis.get('suggested_keywords', [])) or '—'}",
        f"Location: {analysis.get('suggested_location', '—')}",
        "",
        "## Strengths",
        *[f"- {s}" for s in analysis.get("strengths", [])],
        "",
        "## Gaps to fix",
        *[f"- {s}" for s in analysis.get("gaps", [])],
        "",
        "---",
        "",
        "## Resume text",
        "",
        "```",
        text,
        "```",
    ]
    return "\n".join(lines)


def to_txt(text: str, analysis: dict, source: str) -> str:
    md = to_markdown(text, analysis, source)
    return md.replace("#", "").replace("*", "").replace("`", "")


def _latin(text: str) -> str:
    # fpdf2 core fonts are latin-1; map common unicode to ascii equivalents
    return (
        text.replace("→", "->")
        .replace("✓", "v")
        .replace("●", "*")
        .replace("○", "o")
        .encode("latin-1", errors="replace")
        .decode("latin-1")
    )


def to_pdf(text: str, analysis: dict, source: str) -> bytes:
    try:
        from fpdf import FPDF
    except ImportError as e:
        raise RuntimeError(f"PDF export not installed: {e}")
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.multi_cell(0, 10, _latin(f"Resume Analysis — {source}"))
    pdf.set_font("Helvetica", "", 11)
    width = pdf.w - pdf.l_margin - pdf.r_margin
    for line in to_txt(text, analysis, source).splitlines():
        pdf.set_x(pdf.l_margin)
        if not line.strip():
            pdf.ln(4)
            continue
        pdf.multi_cell(width, 6, _latin(line))
    out = pdf.output()
    return bytes(out) if isinstance(out, (bytes, bytearray)) else out.encode("latin-1")
