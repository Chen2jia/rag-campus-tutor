from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import httpx


ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = ROOT / "harness" / "reports" / "latest_llm_config.json"


def assert_status(response: httpx.Response, expected_status: int, label: str) -> None:
    if response.status_code != expected_status:
        raise AssertionError(
            f"{label} expected HTTP {expected_status}, got {response.status_code}: {response.text}"
        )


def write_report(report: dict[str, Any]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


def assert_backend_matches_project(client: httpx.Client) -> None:
    try:
        response = client.get("/openapi.json")
    except httpx.RequestError as exc:
        raise AssertionError(
            "Cannot reach EduMate backend. Start the backend or set EDUMATE_BASE_URL."
        ) from None
    assert_status(response, 200, "openapi")
    paths = set(response.json().get("paths", {}).keys())
    if "/api/llm/status" not in paths:
        raise AssertionError("Target backend does not expose EduMate /api/llm/status")


def assert_no_secret_leak(payload: dict[str, Any]) -> None:
    serialized = json.dumps(payload, ensure_ascii=False).lower()
    forbidden_fragments = ["api_key", "apikey", "secret", "sk-"]
    leaks = [fragment for fragment in forbidden_fragments if fragment in serialized]
    if leaks:
        raise AssertionError(f"LLM status response may leak secrets: {', '.join(leaks)}")


def main() -> None:
    base_url = os.getenv("EDUMATE_BASE_URL", "http://localhost:8000").rstrip("/")
    report: dict[str, Any] = {
        "base_url": base_url,
        "status": "running",
        "checks": [],
    }

    try:
        with httpx.Client(base_url=base_url, timeout=10.0) as client:
            assert_backend_matches_project(client)
            report["checks"].append({"name": "edumate_openapi_preflight", "status": "passed"})

            response = client.get("/api/llm/status")
            assert_status(response, 200, "llm status")
            body = response.json()
            assert_no_secret_leak(body)
            report["llm_status"] = body
            report["checks"].append({"name": "llm_status_no_secret_leak", "status": "passed"})

        report["status"] = "passed"
        write_report(report)
        print("LLM config harness passed.")
    except Exception as exc:
        report["status"] = "failed"
        report["error"] = str(exc)
        write_report(report)
        raise


if __name__ == "__main__":
    main()
