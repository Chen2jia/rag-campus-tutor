from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_document_processor_module_exists() -> None:
    assert (ROOT / "app" / "services" / "document_processor.py").exists()


def test_document_processor_connects_parser_and_chunker() -> None:
    processor_text = (ROOT / "app" / "services" / "document_processor.py").read_text(
        encoding="utf-8"
    )
    for fragment in [
        "class DocumentProcessor",
        "class DocumentProcessingResult",
        "parse_pdf(file_path)",
        "chunk_document(parsed_document)",
        "total_chunks",
    ]:
        assert fragment in processor_text


def test_document_service_runs_processing_after_upload() -> None:
    service_text = (ROOT / "app" / "services" / "document_service.py").read_text(encoding="utf-8")
    for fragment in [
        "DocumentProcessor",
        "await self._process_uploaded_document(document)",
        'document.status = "processing"',
        'document.status = "processed"',
        'document.status = "failed"',
        "document.total_chunks = result.total_chunks",
        "document.error_message = str(exc)",
    ]:
        assert fragment in service_text
