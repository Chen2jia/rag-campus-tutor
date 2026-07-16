from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.rag.chunker import chunk_document
from app.rag.parser import FormulaInfo, ParsedDocument, ParsedPage, TextBlock


def _block(page: int, text: str, block_type: str, formula: FormulaInfo | None = None) -> TextBlock:
    return TextBlock(
        page_number=page,
        text=text,
        bbox=(0.0, 0.0, 100.0, 20.0),
        font_size=12.0,
        font_name="Test",
        is_bold=block_type == "heading",
        is_title_candidate=block_type == "heading",
        block_type=block_type,
        formulas=[formula] if formula else [],
    )


def _formula(page: int, raw: str, latex: str | None, status: str = "recognized") -> FormulaInfo:
    return FormulaInfo(
        raw=raw,
        latex=latex,
        source="native_text",
        confidence=1.0,
        status=status,
        page_number=page,
        bbox=(0.0, 0.0, 100.0, 20.0),
    )


def test_chunker_module_exists() -> None:
    assert (ROOT / "app" / "rag" / "chunker.py").exists()


def test_chunker_preserves_formula_latex_in_chunk_text() -> None:
    formula = _formula(page=1, raw="E = mc²", latex="E = mc^{2}")
    document = ParsedDocument(
        filename="demo.pdf",
        page_count=1,
        pages=[
            ParsedPage(
                page_number=1,
                width=100.0,
                height=100.0,
                text="",
                blocks=[
                    _block(1, "第1章 能量", "heading"),
                    _block(1, "质能方程如下。", "paragraph"),
                    _block(1, "E = mc²", "formula", formula=formula),
                ],
            )
        ],
        title_candidates=[],
        formula_blocks=[],
    )

    chunks = chunk_document(document)

    assert len(chunks) == 1
    assert chunks[0].contains_formula is True
    assert chunks[0].formulas[0].latex == "E = mc^{2}"
    assert "[公式] E = mc^{2}" in chunks[0].text
    assert chunks[0].page_start == 1
    assert chunks[0].page_end == 1
    assert chunks[0].path == "第1章 能量"


def test_chunker_excludes_low_confidence_formula_from_metadata() -> None:
    formula = _formula(page=1, raw="uncertain", latex=None, status="low_confidence")
    document = ParsedDocument(
        filename="demo.pdf",
        page_count=1,
        pages=[
            ParsedPage(
                page_number=1,
                width=100.0,
                height=100.0,
                text="",
                blocks=[
                    _block(1, "说明文字", "paragraph"),
                    _block(1, "uncertain", "formula", formula=formula),
                ],
            )
        ],
        title_candidates=[],
        formula_blocks=[],
    )

    chunks = chunk_document(document)

    assert chunks[0].contains_formula is False
    assert chunks[0].formulas == []
    assert "[公式] uncertain" in chunks[0].text


def test_chunker_static_fragments_exist() -> None:
    chunker_text = (ROOT / "app" / "rag" / "chunker.py").read_text(encoding="utf-8")
    for fragment in ["DocumentChunk", "page_start", "page_end", "contains_formula", "_update_path"]:
        assert fragment in chunker_text
