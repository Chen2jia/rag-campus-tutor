from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    required_paths = [
        "backend/app/routers/rag.py",
        "backend/app/schemas/rag.py",
        "backend/app/services/rag_service.py",
        "backend/app/services/answer_generator.py",
    ]
    missing = [path for path in required_paths if not (ROOT / path).exists()]
    if missing:
        raise SystemExit(f"Missing RAG API paths: {', '.join(missing)}")

    main_text = (ROOT / "backend" / "app" / "main.py").read_text(encoding="utf-8")
    router_text = (ROOT / "backend" / "app" / "routers" / "rag.py").read_text(
        encoding="utf-8"
    )
    schema_text = (ROOT / "backend" / "app" / "schemas" / "rag.py").read_text(
        encoding="utf-8"
    )
    service_text = (ROOT / "backend" / "app" / "services" / "rag_service.py").read_text(
        encoding="utf-8"
    )
    generator_text = (ROOT / "backend" / "app" / "services" / "answer_generator.py").read_text(
        encoding="utf-8"
    )
    config_text = (ROOT / "backend" / "app" / "core" / "config.py").read_text(
        encoding="utf-8"
    )

    required_fragments = [
        "app.include_router(rag.router",
        'router = APIRouter(prefix="/rag", tags=["rag"])',
        '@router.post("/ask", response_model=RagAskResponse)',
        "class RagAskRequest",
        "class RagSource",
        "class RagAskResponse",
        "context_text",
        "is_placeholder: bool = True",
        "answer_provider",
        "model: str | None = None",
        "RetrievalService(db)",
        "retrieval_service.search",
        "AnswerGenerator()",
        "answer_generator.generate",
        "class AnswerGenerator",
        "_openai_is_configured",
        'import_module("openai")',
        "AsyncOpenAI",
        "client.chat.completions.create",
        'openai_model: str = ""',
    ]
    combined_text = "\n".join([main_text, router_text, schema_text, service_text, generator_text, config_text])
    missing_fragments = [fragment for fragment in required_fragments if fragment not in combined_text]
    if missing_fragments:
        raise SystemExit(f"RAG placeholder API missing fragments: {', '.join(missing_fragments)}")

    print("RAG static harness passed.")


if __name__ == "__main__":
    main()
