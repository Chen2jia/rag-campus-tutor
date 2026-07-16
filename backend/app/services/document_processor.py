from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.rag.chunker import DocumentChunk, chunk_document
from app.rag.parser import ParsedDocument, parse_pdf


@dataclass(frozen=True)
class DocumentProcessingResult:
    parsed_document: ParsedDocument
    chunks: list[DocumentChunk]

    @property
    def total_chunks(self) -> int:
        return len(self.chunks)


class DocumentProcessor:
    """Runs the local PDF-to-chunks pipeline before embeddings are introduced."""

    def process_pdf(self, file_path: str | Path) -> DocumentProcessingResult:
        parsed_document = parse_pdf(file_path)
        chunks = chunk_document(parsed_document)
        return DocumentProcessingResult(
            parsed_document=parsed_document,
            chunks=chunks,
        )
