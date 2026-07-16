from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT.parent / "frontend"


def test_frontend_chat_files_exist() -> None:
    expected = [
        FRONTEND / "src" / "components" / "ChatPanel.vue",
        FRONTEND / "src" / "api" / "client.ts",
        FRONTEND / "src" / "App.vue",
    ]
    missing = [path for path in expected if not path.exists()]
    assert missing == []


def test_frontend_chat_panel_and_stream_client_are_wired() -> None:
    app_text = (FRONTEND / "src" / "App.vue").read_text(encoding="utf-8")
    client_text = (FRONTEND / "src" / "api" / "client.ts").read_text(encoding="utf-8")
    panel_text = (FRONTEND / "src" / "components" / "ChatPanel.vue").read_text(
        encoding="utf-8"
    )

    for fragment in [
        'import ChatPanel from "./components/ChatPanel.vue";',
        'type WorkspaceTab = "chat" | "library" | "tasks" | "review" | "plan";',
        'const activeTab = ref<WorkspaceTab>("chat");',
        '{ id: "chat", label: "聊天", count: null }',
        "<ChatPanel",
        ":selected-document-id=\"selectedDocumentId\"",
        ":selected-document-name=\"selectedDocument?.filename ?? ''\"",
        "streamChat(",
        "parseSseEvent",
        "ChatStreamEvent",
    ]:
        assert fragment in app_text + "\n" + client_text + "\n" + panel_text


def test_frontend_chat_panel_uses_sse_events_and_selected_scope() -> None:
    panel_text = (FRONTEND / "src" / "components" / "ChatPanel.vue").read_text(
        encoding="utf-8"
    )
    for fragment in [
        'class="chat-panel"',
        "当前范围",
        "streamChat(props.token, text, props.selectedDocumentId",
        'event: "start"',
        'event: "content"',
        'event: "citations"',
        'event: "done"',
        'event: "error"',
        "messages.value",
        "source-list",
    ]:
        assert fragment in panel_text
