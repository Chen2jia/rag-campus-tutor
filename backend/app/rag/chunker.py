from __future__ import annotations

from dataclasses import dataclass

from app.rag.parser import FormulaInfo, ParsedDocument, TextBlock


@dataclass(frozen=True)
class DocumentChunk:
    chunk_index: int
    path: str
    section: str
    text: str
    page_start: int
    page_end: int
    contains_formula: bool
    formulas: list[FormulaInfo]


def chunk_document(
    document: ParsedDocument,
    target_chars: int = 1800,
    max_chars: int = 2600,
) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []
    current_path: list[str] = []
    current_blocks: list[TextBlock] = []

    for page in document.pages:
        for block in page.blocks:
            if block.block_type == "heading":
                if current_blocks:
                    chunks.append(_build_chunk(len(chunks), current_path, current_blocks))
                    current_blocks = []
                current_path = _update_path(current_path=current_path, heading=block.text)
                continue

            current_blocks.append(block)
            if _blocks_text_length(current_blocks) >= target_chars and not _ends_with_formula(current_blocks):
                chunks.append(_build_chunk(len(chunks), current_path, current_blocks))
                current_blocks = []
            elif _blocks_text_length(current_blocks) >= max_chars:
                chunks.append(_build_chunk(len(chunks), current_path, current_blocks))
                current_blocks = []

    if current_blocks:
        chunks.append(_build_chunk(len(chunks), current_path, current_blocks))

    return chunks


def _build_chunk(
    chunk_index: int,
    current_path: list[str],
    blocks: list[TextBlock],
) -> DocumentChunk:
    page_start = min(block.page_number for block in blocks)
    page_end = max(block.page_number for block in blocks)
    formulas = [formula for block in blocks for formula in block.formulas if formula.status == "recognized"]
    section = current_path[-1] if current_path else f"Page {page_start}"
    path = " > ".join(current_path) if current_path else section

    return DocumentChunk(
        chunk_index=chunk_index,
        path=path,
        section=section,
        text=_format_chunk_text(blocks),
        page_start=page_start,
        page_end=page_end,
        contains_formula=bool(formulas),
        formulas=formulas,
    )


def _format_chunk_text(blocks: list[TextBlock]) -> str:
    lines: list[str] = []
    for block in blocks:
        if block.block_type == "formula":
            formulas = [formula for formula in block.formulas if formula.status == "recognized" and formula.latex]
            if formulas:
                for formula in formulas:
                    lines.append(f"[公式] {formula.latex}")
            else:
                lines.append(f"[公式] {block.text}")
        else:
            lines.append(block.text)
    return "\n".join(line for line in lines if line).strip()


def _update_path(current_path: list[str], heading: str) -> list[str]:
    clean_heading = heading.strip()
    if not clean_heading:
        return current_path

    level = _guess_heading_level(clean_heading)
    next_path = current_path[: max(level - 1, 0)]
    next_path.append(clean_heading)
    return next_path


def _guess_heading_level(heading: str) -> int:
    if heading.startswith(("第", "Chapter", "CHAPTER")):
        return 1
    dot_count = heading.split(" ", 1)[0].count(".")
    if dot_count >= 1:
        return min(dot_count + 1, 3)
    return 2


def _blocks_text_length(blocks: list[TextBlock]) -> int:
    return sum(len(block.text) for block in blocks)


def _ends_with_formula(blocks: list[TextBlock]) -> bool:
    return bool(blocks and blocks[-1].block_type == "formula")
