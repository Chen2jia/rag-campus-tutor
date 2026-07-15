import json
import os
import time
from pathlib import Path
from typing import Any

import httpx


ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = ROOT / "harness" / "reports" / "latest_auth_smoke.json"


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


def main() -> None:
    base_url = os.getenv("EDUMATE_BASE_URL", "http://localhost:8000").rstrip("/")
    suffix = int(time.time() * 1000)
    user_payload = {
        "username": f"harness_{suffix}",
        "email": f"harness_{suffix}@example.com",
        "password": "password123",
    }

    report: dict[str, Any] = {
        "base_url": base_url,
        "checks": [],
        "test_user": {
            "username": user_payload["username"],
            "email": user_payload["email"],
        },
    }

    try:
        with httpx.Client(base_url=base_url, timeout=10.0) as client:
            health = client.get("/api/health")
            assert_status(health, 200, "health")
            report["checks"].append({"name": "health", "status": "passed"})

            unauth_me = client.get("/api/auth/me")
            assert_status(unauth_me, 401, "unauthenticated me")
            report["checks"].append({"name": "unauthenticated_me", "status": "passed"})

            register = client.post("/api/auth/register", json=user_payload)
            assert_status(register, 201, "register")
            register_body = register.json()
            register_token = register_body.get("access_token")
            if not register_token:
                raise AssertionError("register response missing access_token")
            if register_body.get("user", {}).get("email") != user_payload["email"]:
                raise AssertionError("register response user email mismatch")
            report["checks"].append({"name": "register", "status": "passed"})

            login = client.post(
                "/api/auth/login",
                json={"email": user_payload["email"], "password": user_payload["password"]},
            )
            assert_status(login, 200, "login")
            login_body = login.json()
            login_token = login_body.get("access_token")
            if not login_token:
                raise AssertionError("login response missing access_token")
            report["checks"].append({"name": "login", "status": "passed"})

            me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {login_token}"})
            assert_status(me, 200, "authenticated me")
            me_body = me.json()
            if me_body.get("email") != user_payload["email"]:
                raise AssertionError("authenticated /me email mismatch")
            report["checks"].append({"name": "authenticated_me", "status": "passed"})

        report["status"] = "passed"
        write_report(report)
        print("API smoke harness passed.")
    except Exception as exc:
        report["status"] = "failed"
        report["error"] = str(exc)
        write_report(report)
        raise


if __name__ == "__main__":
    main()
