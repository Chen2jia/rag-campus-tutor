from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    required_paths = [
        "backend/app/services/document_processor.py",
        "backend/app/services/document_service.py",
        "backend/app/rag/parser.py",
        "backend/app/rag/chunker.py",
    ]
    missing = [path for path in required_paths if not (ROOT / path).exists()]
    if missing:
        raise SystemExit(f"Missing document processing paths: {', '.join(missing)}")

    processor_text = (ROOT / "backend" / "app" / "services" / "document_processor.py").read_text(
        encoding="utf-8"
    )
    service_text = (ROOT / "backend" / "app" / "services" / "document_service.py").read_text(
        encoding="utf-8"
    )
    required_fragments = [
        "parse_pdf(file_path)",
        "chunk_document(parsed_document)",
        "DocumentProcessingResult",
        "_process_uploaded_document(document)",
        'document.status = "processing"',
        'document.status = "processed"',
        'document.status = "failed"',
        "document.total_chunks = result.total_chunks",
    ]
    combined_text = processor_text + "\n" + service_text
    missing_fragments = [fragment for fragment in required_fragments if fragment not in combined_text]
    if missing_fragments:
        raise SystemExit(
            f"Document processing pipeline missing fragments: {', '.join(missing_fragments)}"
        )

    print("Document processing static harness passed.")


if __name__ == "__main__":
    main()
