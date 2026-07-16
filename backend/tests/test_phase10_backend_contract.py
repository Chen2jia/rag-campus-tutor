from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def assert_contains_all(text: str, fragments: list[str]) -> None:
    missing = [fragment for fragment in fragments if fragment not in text]
    assert missing == []


def test_phase10_auth_contract_covers_register_login_and_current_user() -> None:
    router_text = read("app/routers/auth.py")
    service_text = read("app/services/auth_service.py")
    deps_text = read("app/core/deps.py")
    security_text = read("app/core/security.py")

    assert_contains_all(
        router_text,
        [
            '@router.post("/register"',
            '@router.post("/login"',
            '@router.get("/me"',
            "CurrentUser",
        ],
    )
    assert_contains_all(
        service_text,
        [
            "email = payload.email.strip().lower()",
            "hash_password(payload.password)",
            "verify_password(payload.password, user.password_hash)",
            "HTTP_409_CONFLICT",
            "HTTP_401_UNAUTHORIZED",
            "create_access_token(subject=str(user.id))",
        ],
    )
    assert_contains_all(
        deps_text,
        [
            "OAuth2PasswordBearer",
            "decode_access_token(token)",
            "UUID(raw_user_id)",
            "select(User).where(User.id == user_id)",
        ],
    )
    assert_contains_all(
        security_text,
        [
            "pwd_context.hash",
            "pwd_context.verify",
            "jwt.encode",
            "jwt.decode",
        ],
    )


def test_phase10_business_routes_are_protected_by_current_user() -> None:
    protected_routes = [
        "app/routers/documents.py",
        "app/routers/tasks.py",
        "app/routers/review.py",
        "app/routers/plan.py",
        "app/routers/rag.py",
        "app/routers/chat.py",
    ]

    for route_path in protected_routes:
        route_text = read(route_path)
        assert "CurrentUser" in route_text, route_path
        assert "DbSession" in route_text or route_path == "app/routers/chat.py", route_path


def test_phase10_document_api_contract_covers_upload_search_status_and_delete() -> None:
    router_text = read("app/routers/documents.py")
    service_text = read("app/services/document_service.py")

    assert_contains_all(
        router_text,
        [
            '@router.get("",',
            '@router.post("/upload"',
            '@router.get("/chunks/search"',
            '@router.get("/{task_id}/status"',
            '@router.delete("/{document_id}"',
        ],
    )
    assert_contains_all(
        service_text,
        [
            "Path(settings.upload_dir) / str(user.id)",
            'Path(clean_name).suffix.lower() != ".pdf"',
            "total_size > settings.max_upload_bytes",
            "Document.user_id == user.id",
            "DocumentChunkRecord.user_id == user.id",
            "Document.user_id == user.id",
            "select(Document).where(Document.id == document_id, Document.user_id == user.id)",
            "DocumentVectorIndexer().delete_document_vectors(document)",
            "await self._process_uploaded_document(document)",
        ],
    )


def test_phase10_task_api_contract_covers_crud_and_user_isolation() -> None:
    router_text = read("app/routers/tasks.py")
    service_text = read("app/services/task_service.py")

    assert_contains_all(
        router_text,
        [
            '@router.get("",',
            '@router.post("",',
            '@router.put("/{task_id}"',
            '@router.delete("/{task_id}"',
            "is_done: bool | None",
            "due_date: date | None",
        ],
    )
    assert_contains_all(
        service_text,
        [
            "select(Task).where(Task.user_id == user.id)",
            "select(Task).where(Task.id == task_id, Task.user_id == user.id)",
            "Task.is_done == is_done",
            "Task.due_date == due_date",
            "task.title",
            "task.subject",
            "task.priority",
            "task.due_date",
            "task.is_done",
            "HTTP_404_NOT_FOUND",
        ],
    )


def test_phase10_review_api_contract_covers_today_rate_and_sm2() -> None:
    router_text = read("app/routers/review.py")
    service_text = read("app/services/review_service.py")

    assert_contains_all(
        router_text,
        [
            '@router.post("",',
            '@router.get("/today"',
            '@router.put("/{review_id}/rate"',
        ],
    )
    assert_contains_all(
        service_text,
        [
            "ReviewSchedule.user_id == user.id",
            "ReviewSchedule.next_review_date <= target_date",
            "ReviewSchedule.id == review_id",
            "score < 3",
            "max(1.3",
            "interval_days",
            "ease_factor",
            "next_review_date",
            "HTTP_404_NOT_FOUND",
        ],
    )
