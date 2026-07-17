from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    required_paths = [
        "backend/app/routers/chat.py",
        "backend/app/schemas/chat.py",
        "backend/app/agents/context.py",
        "backend/app/agents/general_agent.py",
        "backend/app/agents/master_agent.py",
        "backend/app/agents/knowledge_agent.py",
        "backend/app/services/rag_service.py",
        "backend/app/main.py",
    ]
    missing = [path for path in required_paths if not (ROOT / path).exists()]
    if missing:
        raise SystemExit(f"Missing chat paths: {', '.join(missing)}")

    main_text = (ROOT / "backend" / "app" / "main.py").read_text(encoding="utf-8")
    router_text = (ROOT / "backend" / "app" / "routers" / "chat.py").read_text(
        encoding="utf-8"
    )
    schema_text = (ROOT / "backend" / "app" / "schemas" / "chat.py").read_text(
        encoding="utf-8"
    )
    agent_text = (ROOT / "backend" / "app" / "agents" / "knowledge_agent.py").read_text(
        encoding="utf-8"
    )
    master_text = (ROOT / "backend" / "app" / "agents" / "master_agent.py").read_text(
        encoding="utf-8"
    )
    general_text = (ROOT / "backend" / "app" / "agents" / "general_agent.py").read_text(
        encoding="utf-8"
    )
    context_text = (ROOT / "backend" / "app" / "agents" / "context.py").read_text(
        encoding="utf-8"
    )

    required_fragments = [
        "app.include_router(chat.router",
        'router = APIRouter(prefix="/chat", tags=["chat"])',
        '@router.post("")',
        "CurrentUser",
        "StreamingResponse",
        'media_type="text/event-stream"',
        "class ChatRequest",
        "message: str",
        "document_id: UUID | None",
        "class AgentContext",
        "from_chat_request",
        "class MasterAgent",
        "GeneralAgent",
        "general_agent.answer",
        "class KnowledgeAgent",
        "RagService(db)",
        "RagAskRequest",
        "stream_answer",
        'self._sse("start"',
        '"content", {',
        '"citations", {',
        'self._sse("done"',
        'self._sse("error"',
        "ensure_ascii=False",
    ]
    combined_text = "\n".join(
        [main_text, router_text, schema_text, agent_text, master_text, general_text, context_text]
    )
    missing_fragments = [fragment for fragment in required_fragments if fragment not in combined_text]
    if missing_fragments:
        raise SystemExit(f"Chat SSE missing fragments: {', '.join(missing_fragments)}")

    print("Chat SSE static harness passed.")


if __name__ == "__main__":
    main()
