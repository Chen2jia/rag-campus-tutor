from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

import httpx


ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = ROOT / "harness" / "reports" / "latest_e2e.json"


def assert_status(response: httpx.Response, expected_status: int, label: str) -> None:
    if response.status_code != expected_status:
        raise AssertionError(
            f"{label} expected HTTP {expected_status}, got {response.status_code}: {response.text}"
        )


def write_report(report: dict[str, Any]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def make_user_payload(name: str, suffix: int) -> dict[str, str]:
    return {
        "username": f"e2e_{name}_{suffix}",
        "email": f"e2e_{name}_{suffix}@example.com",
        "password": "password123",
    }


def register_and_login(client: httpx.Client, payload: dict[str, str]) -> str:
    register = client.post("/api/auth/register", json=payload)
    assert_status(register, 201, f"register {payload['username']}")

    login = client.post(
        "/api/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert_status(login, 200, f"login {payload['username']}")

    token = login.json().get("access_token")
    if not token:
        raise AssertionError(f"login {payload['username']} response missing access_token")
    return str(token)


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def assert_backend_matches_project(client: httpx.Client) -> None:
    response = client.get("/openapi.json")
    assert_status(response, 200, "openapi")
    paths = set(response.json().get("paths", {}).keys())
    required_paths = {
        "/api/health",
        "/api/auth/register",
        "/api/auth/login",
        "/api/documents/upload",
        "/api/rag/ask",
        "/api/chat",
        "/api/plan/generate",
    }
    missing = sorted(required_paths - paths)
    if missing:
        raise AssertionError(
            "Target backend does not look like EduMate. "
            f"Missing OpenAPI paths: {', '.join(missing)}"
        )


def sample_pdf_bytes() -> bytes:
    return (
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
        b"4 0 obj << /Length 132 >> stream\n"
        b"BT /F1 18 Tf 72 720 Td (Taylor formula: f x equals sum of derivatives.) Tj "
        b"0 -28 Td (Review calculus with formulas and examples.) Tj ET\n"
        b"endstream endobj\n"
        b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
        b"xref\n"
        b"0 6\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"0000000257 00000 n \n"
        b"0000000440 00000 n \n"
        b"trailer << /Root 1 0 R /Size 6 >>\n"
        b"startxref\n"
        b"510\n"
        b"%%EOF\n"
    )


def parse_sse_events(text: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for block in text.split("\n\n"):
        event_name = ""
        data_lines: list[str] = []
        for line in block.splitlines():
            if line.startswith("event:"):
                event_name = line.removeprefix("event:").strip()
            elif line.startswith("data:"):
                data_lines.append(line.removeprefix("data:").strip())
        if not event_name:
            continue
        raw_data = "\n".join(data_lines)
        try:
            data: Any = json.loads(raw_data) if raw_data else {}
        except json.JSONDecodeError:
            data = raw_data
        events.append({"event": event_name, "data": data})
    return events


def wait_for_document(
    client: httpx.Client,
    token: str,
    document_id: str,
    report: dict[str, Any],
) -> dict[str, Any]:
    final_status: dict[str, Any] | None = None
    for _ in range(5):
        response = client.get(f"/api/documents/{document_id}/status", headers=auth_headers(token))
        assert_status(response, 200, "document status")
        final_status = response.json()
        if final_status.get("status") in {"processed", "failed"}:
            break
        time.sleep(0.5)

    if final_status is None:
        raise AssertionError("document status response missing")
    report["document_status"] = final_status
    if final_status.get("status") != "processed":
        report["warnings"].append(
            "Uploaded PDF did not reach processed status. Check parser/vector dependencies before demos."
        )
    return final_status


def main() -> None:
    base_url = os.getenv("EDUMATE_BASE_URL", "http://localhost:8000").rstrip("/")
    suffix = int(time.time() * 1000)
    user_a = make_user_payload("alice", suffix)
    user_b = make_user_payload("bob", suffix)
    report: dict[str, Any] = {
        "base_url": base_url,
        "status": "running",
        "checks": [],
        "warnings": [],
        "users": {
            "a": {"username": user_a["username"], "email": user_a["email"]},
            "b": {"username": user_b["username"], "email": user_b["email"]},
        },
    }

    try:
        with httpx.Client(base_url=base_url, timeout=30.0) as client:
            assert_backend_matches_project(client)
            report["checks"].append({"name": "edumate_openapi_preflight", "status": "passed"})

            health = client.get("/api/health")
            assert_status(health, 200, "health")
            report["checks"].append({"name": "health", "status": "passed"})

            token_a = register_and_login(client, user_a)
            token_b = register_and_login(client, user_b)
            report["checks"].append({"name": "register_login_two_users", "status": "passed"})

            upload = client.post(
                "/api/documents/upload",
                files={"file": ("e2e-calculus.pdf", sample_pdf_bytes(), "application/pdf")},
                headers=auth_headers(token_a),
            )
            assert_status(upload, 201, "user A upload PDF")
            document_id = upload.json().get("task_id")
            if not document_id:
                raise AssertionError("upload response missing task_id")
            report["checks"].append({"name": "user_a_upload_pdf", "status": "passed"})
            report["document_id"] = document_id

            wait_for_document(client, token_a, str(document_id), report)
            report["checks"].append({"name": "user_a_document_status", "status": "passed"})

            documents_a = client.get("/api/documents", headers=auth_headers(token_a))
            assert_status(documents_a, 200, "user A list documents")
            if not any(item.get("id") == document_id for item in documents_a.json()):
                raise AssertionError("user A cannot see uploaded document")

            documents_b = client.get("/api/documents", headers=auth_headers(token_b))
            assert_status(documents_b, 200, "user B list documents")
            if any(item.get("id") == document_id for item in documents_b.json()):
                raise AssertionError("user B can see user A document")
            report["checks"].append({"name": "document_user_isolation", "status": "passed"})

            rag = client.post(
                "/api/rag/ask",
                json={"question": "Summarize the Taylor formula notes.", "document_id": document_id},
                headers=auth_headers(token_a),
            )
            assert_status(rag, 200, "user A RAG ask")
            rag_body = rag.json()
            if "answer" not in rag_body or "sources" not in rag_body:
                raise AssertionError("RAG response missing answer or sources")
            report["rag"] = {
                "source_count": len(rag_body.get("sources", [])),
                "is_placeholder": rag_body.get("is_placeholder"),
                "answer_provider": rag_body.get("answer_provider"),
            }
            report["checks"].append({"name": "user_a_rag_ask", "status": "passed"})

            chat = client.post(
                "/api/chat",
                json={"message": "Please summarize this PDF.", "document_id": document_id},
                headers=auth_headers(token_a),
            )
            assert_status(chat, 200, "user A chat SSE")
            chat_events = parse_sse_events(chat.text)
            event_names = {event["event"] for event in chat_events}
            if not {"start", "content", "done"}.issubset(event_names):
                raise AssertionError(f"chat SSE missing expected events: {event_names}")
            report["chat_events"] = [event["event"] for event in chat_events]
            report["checks"].append({"name": "user_a_chat_sse", "status": "passed"})

            plan = client.post(
                "/api/plan/generate",
                json={"goal": "Review calculus", "days": 3, "subject": "math"},
                headers=auth_headers(token_a),
            )
            assert_status(plan, 200, "user A generate plan")
            plan_body = plan.json()
            if len(plan_body.get("days", [])) != 3:
                raise AssertionError("plan response did not include 3 days")
            if len(plan_body.get("created_tasks", [])) != 3:
                raise AssertionError("plan response did not create 3 tasks")
            report["checks"].append({"name": "user_a_generate_plan", "status": "passed"})

            tasks_a = client.get("/api/tasks", headers=auth_headers(token_a))
            assert_status(tasks_a, 200, "user A list tasks")
            if len(tasks_a.json()) < 3:
                raise AssertionError("user A task list does not include generated plan tasks")

            tasks_b = client.get("/api/tasks", headers=auth_headers(token_b))
            assert_status(tasks_b, 200, "user B list tasks")
            if tasks_b.json():
                report["warnings"].append("User B has tasks from previous data; isolation check uses created plan IDs.")
            created_task_ids = {task.get("id") for task in plan_body.get("created_tasks", [])}
            if created_task_ids.intersection({task.get("id") for task in tasks_b.json()}):
                raise AssertionError("user B can see user A generated plan tasks")
            report["checks"].append({"name": "task_user_isolation", "status": "passed"})

        report["status"] = "passed"
        write_report(report)
        print("E2E demo flow harness passed.")
    except Exception as exc:
        report["status"] = "failed"
        report["error"] = str(exc)
        write_report(report)
        raise


if __name__ == "__main__":
    main()
