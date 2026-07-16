from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    required_paths = [
        "frontend/src/App.vue",
        "frontend/src/api/client.ts",
        "frontend/package.json",
    ]
    missing = [path for path in required_paths if not (ROOT / path).exists()]
    if missing:
        raise SystemExit(f"Missing frontend RAG paths: {', '.join(missing)}")

    app_text = (ROOT / "frontend" / "src" / "App.vue").read_text(encoding="utf-8")
    client_text = (ROOT / "frontend" / "src" / "api" / "client.ts").read_text(encoding="utf-8")
    required_fragments = [
        "VITE_API_BASE_URL",
        "edumate_token",
        "Authorization",
        "login(",
        "register(",
        "listDocuments(",
        "uploadDocument(",
        "/documents/upload",
        "searchDocumentChunks(",
        "/documents/chunks/search",
        "askRag(",
        "/rag/ask",
        "selectedDocumentId",
        "ragAnswer",
        "searchResults",
    ]
    combined_text = app_text + "\n" + client_text
    missing_fragments = [fragment for fragment in required_fragments if fragment not in combined_text]
    if missing_fragments:
        raise SystemExit(f"Frontend RAG workspace missing fragments: {', '.join(missing_fragments)}")

    print("Frontend RAG static harness passed.")


if __name__ == "__main__":
    main()
