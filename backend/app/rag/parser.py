from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from statistics import median
from typing import Any

from app.rag.formula_normalizer import looks_like_formula, normalize_formula_to_latex


@dataclass(frozen=True)
class FormulaInfo:
    raw: str
    latex: str | None
    source: str
    confidence: float
    status: str
    page_number: int
    bbox: tuple[float, float, float, float]


@dataclass(frozen=True)
class TextBlock:
    page_number: int
    text: str
    bbox: tuple[float, float, float, float]
    font_size: float
    font_name: str
    is_bold: bool
    is_title_candidate: bool
    block_type: str
    formulas: list[FormulaInfo]


@dataclass(frozen=True)
class ParsedPage:
    page_number: int
    width: float
    height: float
    text: str
    blocks: list[TextBlock]


@dataclass(frozen=True)
class ParsedDocument:
    filename: str
    page_count: int
    pages: list[ParsedPage]
    title_candidates: list[TextBlock]
    formula_blocks: list[TextBlock]


def parse_pdf(file_path: str | Path) -> ParsedDocument:
    """Extract text and lightweight layout signals from a PDF file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are supported")

    fitz = _load_fitz()
    document = fitz.open(path)
    try:
        pages = [_parse_page(page, page_index + 1) for page_index, page in enumerate(document)]
    finally:
        document.close()

    title_candidates = [
        block
        for page in pages
        for block in page.blocks
        if block.is_title_candidate
    ]
    formula_blocks = [
        block
        for page in pages
        for block in page.blocks
        if block.block_type == "formula"
    ]
    return ParsedDocument(
        filename=path.name,
        page_count=len(pages),
        pages=pages,
        title_candidates=title_candidates,
        formula_blocks=formula_blocks,
    )


def _load_fitz() -> Any:
    try:
        return import_module("fitz")
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "PyMuPDF is required to parse PDFs. Install project requirements first."
        ) from exc


def _parse_page(page: Any, page_number: int) -> ParsedPage:
    page_dict = page.get_text("dict")
    blocks = _extract_text_blocks(page_dict=page_dict, page_number=page_number)
    page_text = "\n".join(block.text for block in blocks if block.text)
    rect = page.rect
    return ParsedPage(
        page_number=page_number,
        width=float(rect.width),
        height=float(rect.height),
        text=page_text,
        blocks=blocks,
    )


def _extract_text_blocks(page_dict: dict[str, Any], page_number: int) -> list[TextBlock]:
    raw_blocks: list[dict[str, Any]] = []
    for block in page_dict.get("blocks", []):
        if block.get("type") != 0:
            continue

        lines = block.get("lines", [])
        text_parts: list[str] = []
        sizes: list[float] = []
        fonts: list[str] = []

        for line in lines:
            line_text, line_sizes, line_fonts = _extract_line(line)
            if line_text:
                text_parts.append(line_text)
            sizes.extend(line_sizes)
            fonts.extend(line_fonts)

        text = " ".join(text_parts).strip()
        if not text:
            continue

        raw_blocks.append(
            {
                "page_number": page_number,
                "text": text,
                "bbox": tuple(float(value) for value in block.get("bbox", (0, 0, 0, 0))),
                "font_size": max(sizes) if sizes else 0.0,
                "font_name": fonts[0] if fonts else "",
                "is_bold": any(_font_is_bold(font) for font in fonts),
            }
        )

    body_font_size = _estimate_body_font_size([block["font_size"] for block in raw_blocks])
    return [
        _build_text_block(block=block, body_font_size=body_font_size)
        for block in raw_blocks
    ]


def _build_text_block(block: dict[str, Any], body_font_size: float) -> TextBlock:
    is_title_candidate = _is_likely_title(
        text=block["text"],
        font_size=block["font_size"],
        body_font_size=body_font_size,
        is_bold=block["is_bold"],
    )
    is_formula_candidate = _is_formula_candidate(
        text=block["text"],
        is_title_candidate=is_title_candidate,
    )
    block_type = "formula" if is_formula_candidate else "heading" if is_title_candidate else "paragraph"
    formulas = [
        _build_native_formula_info(
            text=block["text"],
            page_number=block["page_number"],
            bbox=block["bbox"],
        )
    ] if is_formula_candidate else []

    return TextBlock(
        page_number=block["page_number"],
        text=block["text"],
        bbox=block["bbox"],
        font_size=block["font_size"],
        font_name=block["font_name"],
        is_bold=block["is_bold"],
        is_title_candidate=is_title_candidate,
        block_type=block_type,
        formulas=formulas,
    )


def _extract_line(line: dict[str, Any]) -> tuple[str, list[float], list[str]]:
    text_parts: list[str] = []
    sizes: list[float] = []
    fonts: list[str] = []

    for span in line.get("spans", []):
        text = str(span.get("text", "")).strip()
        if text:
            text_parts.append(text)
        if "size" in span:
            sizes.append(float(span["size"]))
        if "font" in span:
            fonts.append(str(span["font"]))

    return " ".join(text_parts).strip(), sizes, fonts


def _estimate_body_font_size(font_sizes: list[float]) -> float:
    meaningful_sizes = [size for size in font_sizes if size > 0]
    if not meaningful_sizes:
        return 0.0
    return float(median(meaningful_sizes))


def _font_is_bold(font_name: str) -> bool:
    normalized = font_name.lower()
    return "bold" in normalized or "black" in normalized or "heavy" in normalized


def _is_likely_title(
    text: str,
    font_size: float,
    body_font_size: float,
    is_bold: bool,
) -> bool:
    clean_text = text.strip()
    if not clean_text:
        return False
    if len(clean_text) > 120:
        return False

    size_lift = font_size >= body_font_size * 1.18 if body_font_size else False
    numbered_heading = clean_text[:4].strip().rstrip(".").isdigit()
    chapter_heading = clean_text.startswith(("第", "Chapter", "CHAPTER"))
    return size_lift or is_bold or numbered_heading or chapter_heading


def _is_formula_candidate(text: str, is_title_candidate: bool) -> bool:
    if is_title_candidate and not any(symbol in text for symbol in ("=", "∑", "∫", "√")):
        return False
    return looks_like_formula(text)


def _build_native_formula_info(
    text: str,
    page_number: int,
    bbox: tuple[float, float, float, float],
) -> FormulaInfo:
    latex = normalize_formula_to_latex(text)
    return FormulaInfo(
        raw=text,
        latex=latex,
        source="native_text",
        confidence=1.0,
        status="recognized",
        page_number=page_number,
        bbox=bbox,
    )
