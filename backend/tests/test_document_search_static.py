from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_document_search_schema_exists() -> None:
    schema_text = (ROOT / "app" / "schemas" / "document.py").read_text(encoding="utf-8")
    for fragment in [
        "class DocumentChunkSearchResult",
        "class DocumentChunkSearchResponse",
        "document_id",
        "filename",
        "chunk_index",
        "formulas_metadata",
        "results: list[DocumentChunkSearchResult]",
    ]:
        assert fragment in schema_text


def test_document_search_route_is_registered_before_dynamic_status_route() -> None:
    router_text = (ROOT / "app" / "routers" / "documents.py").read_text(encoding="utf-8")
    assert '@router.get("/chunks/search"' in router_text
    assert "DocumentChunkSearchResponse" in router_text
    assert "q: str = Query(..., min_length=1)" in router_text
    assert "limit: int = Query(10, ge=1, le=20)" in router_text
    assert router_text.index('@router.get("/chunks/search"') < router_text.index(
        '@router.get("/{task_id}/status"'
    )


def test_document_search_service_filters_by_current_user() -> None:
    service_text = (ROOT / "app" / "services" / "document_service.py").read_text(encoding="utf-8")
    for fragment in [
        "async def search_chunks",
        "DocumentChunkRecord.user_id == user.id",
        "Document.user_id == user.id",
        "DocumentChunkRecord.text.ilike(like_query)",
        "DocumentChunkRecord.path.ilike(like_query)",
        "DocumentChunkRecord.section.ilike(like_query)",
        "DocumentChunkSearchResult",
    ]:
        assert fragment in service_text
