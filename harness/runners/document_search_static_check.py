from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    required_paths = [
        "backend/app/routers/documents.py",
        "backend/app/services/document_service.py",
        "backend/app/schemas/document.py",
        "backend/app/models/document_chunk.py",
    ]
    missing = [path for path in required_paths if not (ROOT / path).exists()]
    if missing:
        raise SystemExit(f"Missing document search paths: {', '.join(missing)}")

    router_text = (ROOT / "backend" / "app" / "routers" / "documents.py").read_text(
        encoding="utf-8"
    )
    service_text = (ROOT / "backend" / "app" / "services" / "document_service.py").read_text(
        encoding="utf-8"
    )
    schema_text = (ROOT / "backend" / "app" / "schemas" / "document.py").read_text(
        encoding="utf-8"
    )

    required_fragments = [
        '@router.get("/chunks/search"',
        "DocumentChunkSearchResponse",
        "async def search_chunks",
        "DocumentChunkRecord.user_id == user.id",
        "Document.user_id == user.id",
        "DocumentChunkRecord.text.ilike(like_query)",
        "DocumentChunkRecord.path.ilike(like_query)",
        "DocumentChunkRecord.section.ilike(like_query)",
        "formulas_metadata",
    ]
    combined_text = router_text + "\n" + service_text + "\n" + schema_text
    missing_fragments = [fragment for fragment in required_fragments if fragment not in combined_text]
    if missing_fragments:
        raise SystemExit(f"Document search missing fragments: {', '.join(missing_fragments)}")

    if router_text.index('@router.get("/chunks/search"') > router_text.index(
        '@router.get("/{task_id}/status"'
    ):
        raise SystemExit("Document search route must be declared before dynamic status route")

    print("Document search static harness passed.")


if __name__ == "__main__":
    main()
