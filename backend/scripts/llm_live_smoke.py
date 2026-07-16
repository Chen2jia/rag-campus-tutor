from __future__ import annotations

import asyncio
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.llm_service import LlmService


REPORT_PATH = (
    Path("../harness/reports/latest_llm_live_smoke.json")
    if Path.cwd().name.lower() == "backend"
    else Path("harness/reports/latest_llm_live_smoke.json")
)


def redact(value: str) -> str:
    value = re.sub(r"sk-[A-Za-z0-9_\-]{8,}", "sk-***", value)
    value = re.sub(r"(api[_-]?key['\"]?\s*[:=]\s*['\"]?)[^'\"\s,]+", r"\1***", value, flags=re.I)
    return value


def safe_error(exc: Exception) -> str:
    return redact(f"{exc.__class__.__name__}: {exc}")


def write_report(report: dict[str, Any]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


async def main() -> None:
    service = LlmService()
    status = service.config_status()
    report: dict[str, Any] = {
        "status": "running",
        "configured": status.configured,
        "provider": status.provider,
        "model": status.model,
        "base_url_host": status.base_url_host,
        "missing": status.missing,
        "checks": [],
    }

    try:
        if not status.configured:
            raise RuntimeError(f"LLM is not configured. Missing: {', '.join(status.missing)}")

        response = await service.generate(
            messages=[
                {
                    "role": "system",
                    "content": "You are a connectivity check. Reply with exactly: PONG",
                },
                {"role": "user", "content": "Return PONG."},
            ],
            temperature=0,
        )
        content = response.content.strip()
        report["response_preview"] = redact(content[:120])
        report["checks"].append({"name": "llm_generate_non_empty", "status": "passed"})
        if "pong" not in content.lower():
            report["warnings"] = ["Model responded, but did not include PONG exactly."]

        report["status"] = "passed"
        write_report(report)
        print("LLM live smoke passed.")
    except Exception as exc:
        report["status"] = "failed"
        report["error"] = safe_error(exc)
        write_report(report)
        raise RuntimeError(report["error"]) from None


if __name__ == "__main__":
    asyncio.run(main())
