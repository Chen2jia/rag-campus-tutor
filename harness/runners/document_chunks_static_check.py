from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    required_paths = [
        "backend/app/models/document_chunk.py",
        "backend/alembic/versions/202607160002_create_document_chunks.py",
        "backend/app/services/document_service.py",
    ]
    missing = [path for path in required_paths if not (ROOT / path).exists()]
    if missing:
        raise SystemExit(f"Missing document chunk paths: {', '.join(missing)}")

    model_text = (ROOT / "backend" / "app" / "models" / "document_chunk.py").read_text(
        encoding="utf-8"
    )
    service_text = (ROOT / "backend" / "app" / "services" / "document_service.py").read_text(
        encoding="utf-8"
    )
    migration_text = (
        ROOT / "backend" / "alembic" / "versions" / "202607160002_create_document_chunks.py"
    ).read_text(encoding="utf-8")

    required_fragments = [
        "DocumentChunkRecord",
        "document_chunks",
        "user_id",
        "document_id",
        "chunk_index",
        "formulas_metadata",
        "uq_document_chunks_document_index",
        "_replace_document_chunks",
        "_serialize_formulas",
        "DocumentChunkRecord.user_id == document.user_id",
    ]
    combined_text = model_text + "\n" + service_text + "\n" + migration_text
    missing_fragments = [fragment for fragment in required_fragments if fragment not in combined_text]
    if missing_fragments:
        raise SystemExit(f"Document chunk persistence missing fragments: {', '.join(missing_fragments)}")

    print("Document chunks static harness passed.")


if __name__ == "__main__":
    main()
