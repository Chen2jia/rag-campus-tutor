from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_rag_api_files_exist() -> None:
    expected = [
        "app/routers/rag.py",
        "app/schemas/rag.py",
        "app/services/rag_service.py",
    ]
    missing = [path for path in expected if not (ROOT / path).exists()]
    assert missing == []


def test_rag_router_is_registered() -> None:
    main_text = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
    assert "rag" in main_text
    assert "app.include_router(rag.router" in main_text


def test_rag_route_matches_placeholder_surface() -> None:
    router_text = (ROOT / "app" / "routers" / "rag.py").read_text(encoding="utf-8")
    assert 'router = APIRouter(prefix="/rag", tags=["rag"])' in router_text
    assert '@router.post("/ask", response_model=RagAskResponse)' in router_text
    assert "RagService(db).ask(current_user, payload)" in router_text


def test_rag_schema_contains_sources_and_context() -> None:
    schema_text = (ROOT / "app" / "schemas" / "rag.py").read_text(encoding="utf-8")
    for fragment in [
        "class RagAskRequest",
        "question: str",
        "document_id: UUID | None",
        "class RagSource",
        "page_start",
        "page_end",
        "contains_formula",
        "class RagAskResponse",
        "sources: list[RagSource]",
        "context_text: str",
        "is_placeholder: bool = True",
        'answer_provider: str = "placeholder"',
        "model: str | None = None",
    ]:
        assert fragment in schema_text


def test_rag_service_reuses_document_chunk_search() -> None:
    service_text = (ROOT / "app" / "services" / "rag_service.py").read_text(encoding="utf-8")
    for fragment in [
        "class RagService",
        "DocumentService(db)",
        "AnswerGenerator()",
        "search_chunks",
        "query_text=question",
        "document_id=payload.document_id",
        "_format_context",
        "answer_generator.generate",
        "answer_provider=generated_answer.answer_provider",
    ]:
        assert fragment in service_text
