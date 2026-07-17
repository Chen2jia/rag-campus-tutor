from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_chat_api_files_exist() -> None:
    expected = [
        "app/routers/chat.py",
        "app/schemas/chat.py",
        "app/agents/context.py",
        "app/agents/general_agent.py",
        "app/agents/knowledge_agent.py",
    ]
    missing = [path for path in expected if not (ROOT / path).exists()]
    assert missing == []


def test_chat_router_is_registered_and_streams_sse() -> None:
    main_text = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
    router_text = (ROOT / "app" / "routers" / "chat.py").read_text(encoding="utf-8")
    for fragment in [
        "chat",
        "app.include_router(chat.router",
        'router = APIRouter(prefix="/chat", tags=["chat"])',
        '@router.post("")',
        "CurrentUser",
        "DbSession",
        "StreamingResponse",
        "MasterAgent(db).stream_answer(current_user, payload)",
        'media_type="text/event-stream"',
        '"Cache-Control": "no-cache"',
        '"X-Accel-Buffering": "no"',
    ]:
        assert fragment in main_text + "\n" + router_text


def test_chat_schema_supports_message_limit_and_document_scope() -> None:
    schema_text = (ROOT / "app" / "schemas" / "chat.py").read_text(encoding="utf-8")
    for fragment in [
        "class ChatRequest",
        "message: str",
        "limit: int",
        "document_id: UUID | None",
        "min_length=1",
        "max_length=1000",
    ]:
        assert fragment in schema_text


def test_knowledge_agent_wraps_rag_and_sse_events() -> None:
    agent_text = (ROOT / "app" / "agents" / "knowledge_agent.py").read_text(encoding="utf-8")
    for fragment in [
        "class KnowledgeAgent",
        "RagService(db)",
        "RagAskRequest",
        "question=payload.message",
        "document_id=payload.document_id",
        "async def stream_answer",
        'self._sse("start"',
        '"content", {',
        '"citations", {',
        'self._sse("done"',
        'self._sse("error"',
        "json.dumps",
        "ensure_ascii=False",
    ]:
        assert fragment in agent_text


def test_master_agent_uses_agent_context_and_general_agent() -> None:
    master_text = (ROOT / "app" / "agents" / "master_agent.py").read_text(encoding="utf-8")
    general_text = (ROOT / "app" / "agents" / "general_agent.py").read_text(encoding="utf-8")
    context_text = (ROOT / "app" / "agents" / "context.py").read_text(encoding="utf-8")
    combined = "\n".join([master_text, general_text, context_text])
    for fragment in [
        "class AgentContext",
        "from_chat_request",
        "class GeneralAgent",
        "LlmService",
        "general_agent.answer",
        "detect_intent",
        "ChatIntent.general",
        "ChatIntent.knowledge",
        "ChatIntent.plan",
        "ensure_ascii=False",
    ]:
        assert fragment in combined
