from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    required_paths = [
        "frontend/src/App.vue",
        "frontend/src/api/client.ts",
        "frontend/src/components/ChatPanel.vue",
        "frontend/package.json",
    ]
    missing = [path for path in required_paths if not (ROOT / path).exists()]
    if missing:
        raise SystemExit(f"Missing frontend chat paths: {', '.join(missing)}")

    app_text = (ROOT / "frontend" / "src" / "App.vue").read_text(encoding="utf-8")
    client_text = (ROOT / "frontend" / "src" / "api" / "client.ts").read_text(encoding="utf-8")
    panel_text = (ROOT / "frontend" / "src" / "components" / "ChatPanel.vue").read_text(
        encoding="utf-8"
    )
    required_fragments = [
        "VITE_API_BASE_URL",
        "streamChat(",
        "parseSseEvent",
        "ChatStreamEvent",
        'import ChatPanel from "./components/ChatPanel.vue";',
        'type WorkspaceTab = "chat" | "library" | "tasks" | "review" | "plan";',
        'const activeTab = ref<WorkspaceTab>("chat");',
        '{ id: "chat", label: "聊天", count: null }',
        "<ChatPanel",
        ":selected-document-id=\"selectedDocumentId\"",
        ":selected-document-name=\"selectedDocument?.filename ?? ''\"",
        'class="chat-panel"',
        "当前范围",
        'streamChat(props.token, text, props.selectedDocumentId',
        'event: "start"',
        'event: "content"',
        'event: "citations"',
        'event: "done"',
        'event: "error"',
    ]
    combined_text = app_text + "\n" + client_text + "\n" + panel_text
    missing_fragments = [fragment for fragment in required_fragments if fragment not in combined_text]
    if missing_fragments:
        raise SystemExit(f"Frontend chat workspace missing fragments: {', '.join(missing_fragments)}")

    print("Frontend chat static harness passed.")


if __name__ == "__main__":
    main()
