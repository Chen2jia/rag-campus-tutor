from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    required_paths = [
        "frontend/src/App.vue",
        "frontend/src/api/client.ts",
        "frontend/src/components/AuthPanel.vue",
        "frontend/src/components/DocumentLibraryPanel.vue",
        "frontend/src/components/PlanPanel.vue",
        "frontend/src/components/ReviewPanel.vue",
        "frontend/src/components/TaskPanel.vue",
        "frontend/package.json",
    ]
    missing = [path for path in required_paths if not (ROOT / path).exists()]
    if missing:
        raise SystemExit(f"Missing frontend RAG paths: {', '.join(missing)}")

    app_text = (ROOT / "frontend" / "src" / "App.vue").read_text(encoding="utf-8")
    client_text = (ROOT / "frontend" / "src" / "api" / "client.ts").read_text(encoding="utf-8")
    auth_panel_text = (
        ROOT / "frontend" / "src" / "components" / "AuthPanel.vue"
    ).read_text(encoding="utf-8")
    document_panel_text = (
        ROOT / "frontend" / "src" / "components" / "DocumentLibraryPanel.vue"
    ).read_text(encoding="utf-8")
    plan_panel_text = (
        ROOT / "frontend" / "src" / "components" / "PlanPanel.vue"
    ).read_text(encoding="utf-8")
    review_panel_text = (
        ROOT / "frontend" / "src" / "components" / "ReviewPanel.vue"
    ).read_text(encoding="utf-8")
    task_panel_text = (ROOT / "frontend" / "src" / "components" / "TaskPanel.vue").read_text(
        encoding="utf-8"
    )
    required_fragments = [
        "VITE_API_BASE_URL",
        "edumate_token",
        "Authorization",
        "login(",
        "register(",
        "listDocuments(",
        "uploadDocument(",
        "/documents/upload",
        "getDocumentStatus(",
        "/status",
        "deleteDocument(",
        "deleteDocumentItem",
        "searchDocumentChunks(",
        "/documents/chunks/search",
        "askRag(",
        "/rag/ask",
        "listTasks(",
        "createTask(",
        "updateTask(",
        "deleteTask(",
        "/tasks",
        "listTodayReviews(",
        "createReview(",
        "rateReview(",
        "/review/today",
        "generatePlan(",
        "/plan/generate",
        "selectedDocumentId",
        "activeTab",
        "AuthPanel",
        "DocumentLibraryPanel",
        "PlanPanel",
        "ReviewPanel",
        "TaskPanel",
        "submitTask",
        "submitReview",
        "submitPlan",
        "waitForDocumentProcessing",
        "pollingStatus",
        "ragAnswer",
        "searchResults",
    ]
    combined_text = "\n".join(
        [
            app_text,
            client_text,
            auth_panel_text,
            document_panel_text,
            plan_panel_text,
            review_panel_text,
            task_panel_text,
        ]
    )
    missing_fragments = [fragment for fragment in required_fragments if fragment not in combined_text]
    if missing_fragments:
        raise SystemExit(f"Frontend RAG workspace missing fragments: {', '.join(missing_fragments)}")

    print("Frontend RAG static harness passed.")


if __name__ == "__main__":
    main()
