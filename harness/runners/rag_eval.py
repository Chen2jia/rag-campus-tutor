from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

import httpx


ROOT = Path(__file__).resolve().parents[2]
EVAL_PATH = ROOT / "harness" / "evals" / "rag_eval_cases.json"
REPORT_PATH = ROOT / "harness" / "reports" / "latest_rag_eval.json"


def assert_status(response: httpx.Response, expected_status: int, label: str) -> None:
    if response.status_code != expected_status:
        raise AssertionError(
            f"{label} expected HTTP {expected_status}, got {response.status_code}: {response.text}"
        )


def write_report(report: dict[str, Any]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def register_and_login(client: httpx.Client) -> str:
    suffix = int(time.time() * 1000)
    payload = {
        "username": f"rag_eval_{suffix}",
        "email": f"rag_eval_{suffix}@example.com",
        "password": "password123",
    }
    register = client.post("/api/auth/register", json=payload)
    assert_status(register, 201, "register rag eval user")
    login = client.post(
        "/api/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert_status(login, 200, "login rag eval user")
    token = login.json().get("access_token")
    if not token:
        raise AssertionError("login response missing access_token")
    return str(token)


def assert_backend_matches_project(client: httpx.Client) -> None:
    try:
        response = client.get("/openapi.json")
    except httpx.RequestError:
        raise AssertionError(
            "Cannot reach EduMate backend. Start the backend or set EDUMATE_BASE_URL."
        ) from None
    assert_status(response, 200, "openapi")
    paths = set(response.json().get("paths", {}).keys())
    required = {
        "/api/auth/register",
        "/api/auth/login",
        "/api/documents/upload",
        "/api/documents/{task_id}/status",
        "/api/rag/ask",
    }
    missing = sorted(required - paths)
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
        b"4 0 obj << /Length 252 >> stream\n"
        b"BT /F1 16 Tf 72 720 Td (Calculus notes about Taylor formula.) Tj "
        b"0 -24 Td (The Taylor formula uses derivatives to approximate a function.) Tj "
        b"0 -24 Td (A supported LaTeX form is f(x)=sum a_n x^n.) Tj "
        b"0 -24 Td (If a formula image is unclear, do not invent LaTeX.) Tj ET\n"
        b"endstream endobj\n"
        b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
        b"xref\n"
        b"0 6\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"0000000257 00000 n \n"
        b"0000000560 00000 n \n"
        b"trailer << /Root 1 0 R /Size 6 >>\n"
        b"startxref\n"
        b"630\n"
        b"%%EOF\n"
    )


def wait_for_document(client: httpx.Client, token: str, document_id: str) -> dict[str, Any]:
    final_status: dict[str, Any] | None = None
    for _ in range(10):
        response = client.get(f"/api/documents/{document_id}/status", headers=auth_headers(token))
        assert_status(response, 200, "document status")
        final_status = response.json()
        if final_status.get("status") in {"processed", "failed"}:
            break
        time.sleep(0.5)
    if not final_status:
        raise AssertionError("document status response missing")
    return final_status


def load_cases() -> list[dict[str, Any]]:
    payload = json.loads(EVAL_PATH.read_text(encoding="utf-8"))
    cases = payload.get("cases")
    if not isinstance(cases, list):
        raise AssertionError("RAG eval file does not contain cases list")
    return cases


def contains_all(text: str, terms: list[str]) -> bool:
    lowered = text.lower()
    return all(term.lower() in lowered for term in terms)


def score_case(case: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    answer = str(response.get("answer", ""))
    context_text = str(response.get("context_text", ""))
    combined_text = f"{answer}\n{context_text}"
    sources = response.get("sources", [])
    if not isinstance(sources, list):
        sources = []

    checks: list[dict[str, Any]] = []
    for check_name in case["checks"]:
        passed = True
        detail = ""
        if check_name == "answer_mentions_expected_keywords":
            passed = contains_all(combined_text, case["expected_keywords"])
            detail = "expected keywords must appear in answer or retrieved context"
        elif check_name == "has_citation_source":
            passed = len(sources) >= int(case["min_sources"])
            detail = f"expected at least {case['min_sources']} sources"
        elif check_name == "does_not_invent_formula":
            passed = (
                "latex" in combined_text.lower()
                or "formula" in combined_text.lower()
                or bool(sources)
            )
            detail = "formula answer should be grounded in retrieved context"
        elif check_name == "safe_no_context_fallback":
            passed = len(sources) <= int(case["min_sources"])
            detail = "fallback case should not retrieve unrelated sources"
        else:
            passed = False
            detail = f"unknown check: {check_name}"
        checks.append({"name": check_name, "passed": passed, "detail": detail})

    passed = all(check["passed"] for check in checks)
    return {
        "id": case["id"],
        "category": case["category"],
        "question": case["question"],
        "passed": passed,
        "checks": checks,
        "source_count": len(sources),
        "is_placeholder": response.get("is_placeholder"),
        "answer_provider": response.get("answer_provider"),
        "answer_preview": answer[:240],
    }


def main() -> None:
    base_url = os.getenv("EDUMATE_BASE_URL", "http://localhost:8000").rstrip("/")
    strict = os.getenv("RAG_EVAL_STRICT", "").lower() in {"1", "true", "yes"}
    report: dict[str, Any] = {
        "base_url": base_url,
        "status": "running",
        "strict": strict,
        "cases": [],
        "warnings": [],
    }

    try:
        cases = load_cases()
        with httpx.Client(base_url=base_url, timeout=30.0) as client:
            assert_backend_matches_project(client)
            token = register_and_login(client)

            upload = client.post(
                "/api/documents/upload",
                files={"file": ("rag-eval-calculus.pdf", sample_pdf_bytes(), "application/pdf")},
                headers=auth_headers(token),
            )
            assert_status(upload, 201, "upload rag eval PDF")
            document_id = upload.json().get("task_id")
            if not document_id:
                raise AssertionError("upload response missing task_id")

            document_status = wait_for_document(client, token, str(document_id))
            report["document_status"] = document_status
            if document_status.get("status") != "processed":
                report["warnings"].append("Uploaded eval PDF did not reach processed status.")

            for case in cases:
                document_scope = None if case["category"] == "fallback" else document_id
                rag_response = client.post(
                    "/api/rag/ask",
                    json={
                        "question": case["question"],
                        "limit": 5,
                        "document_id": document_scope,
                    },
                    headers=auth_headers(token),
                )
                assert_status(rag_response, 200, f"RAG eval case {case['id']}")
                report["cases"].append(score_case(case, rag_response.json()))

        failed = [case for case in report["cases"] if not case["passed"]]
        report["summary"] = {
            "total": len(report["cases"]),
            "passed": len(report["cases"]) - len(failed),
            "failed": len(failed),
        }
        report["status"] = "failed" if failed else "passed"
        write_report(report)

        if failed and strict:
            raise AssertionError(f"RAG eval failed {len(failed)} case(s) in strict mode")
        print("RAG eval harness completed.")
    except Exception as exc:
        report["status"] = "error"
        report["error"] = str(exc)
        write_report(report)
        raise


if __name__ == "__main__":
    main()
