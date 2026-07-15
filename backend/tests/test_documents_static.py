from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_document_api_files_exist() -> None:
    expected = [
        "app/routers/documents.py",
        "app/services/document_service.py",
        "app/schemas/document.py",
    ]
    missing = [path for path in expected if not (ROOT / path).exists()]
    assert missing == []


def test_document_router_is_registered() -> None:
    main_text = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
    assert "from app.routers import auth, documents, health" in main_text
    assert "app.include_router(documents.router" in main_text


def test_document_routes_match_prd_surface() -> None:
    router_text = (ROOT / "app" / "routers" / "documents.py").read_text(encoding="utf-8")
    for route_fragment in [
        '@router.get("",',
        '@router.post("/upload"',
        '@router.get("/{task_id}/status"',
        '@router.delete("/{document_id}"',
    ]:
        assert route_fragment in router_text


def test_document_service_filters_by_current_user() -> None:
    service_text = (ROOT / "app" / "services" / "document_service.py").read_text(encoding="utf-8")
    assert "Document.user_id == user.id" in service_text
    assert "select(Document).where(Document.id == document_id, Document.user_id == user.id)" in service_text


def test_document_upload_constraints_are_defined() -> None:
    config_text = (ROOT / "app" / "core" / "config.py").read_text(encoding="utf-8")
    service_text = (ROOT / "app" / "services" / "document_service.py").read_text(encoding="utf-8")
    assert "max_upload_bytes" in config_text
    assert 'Path(clean_name).suffix.lower() != ".pdf"' in service_text
    assert "HTTP_413_REQUEST_ENTITY_TOO_LARGE" in service_text
