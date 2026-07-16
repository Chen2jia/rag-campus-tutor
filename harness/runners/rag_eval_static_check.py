from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
EVAL_PATH = ROOT / "harness" / "evals" / "rag_eval_cases.json"
REQUIRED_CHECKS = {
    "answer_mentions_expected_keywords",
    "has_citation_source",
    "does_not_invent_formula",
    "safe_no_context_fallback",
}


def load_eval() -> dict[str, Any]:
    if not EVAL_PATH.exists():
        raise SystemExit(f"Missing RAG eval file: {EVAL_PATH}")
    return json.loads(EVAL_PATH.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def validate_case(case: dict[str, Any], seen_ids: set[str]) -> None:
    required_fields = {
        "id",
        "category",
        "question",
        "expected_keywords",
        "required_source_terms",
        "min_sources",
        "checks",
        "notes",
    }
    missing = sorted(required_fields - set(case))
    require(not missing, f"RAG eval case missing fields: {case.get('id', '<unknown>')} {missing}")

    case_id = case["id"]
    require(isinstance(case_id, str) and case_id.strip(), "RAG eval case id must be non-empty")
    require(case_id not in seen_ids, f"Duplicate RAG eval case id: {case_id}")
    seen_ids.add(case_id)

    require(isinstance(case["question"], str) and len(case["question"].strip()) >= 8, f"{case_id} question is too short")
    require(isinstance(case["expected_keywords"], list), f"{case_id} expected_keywords must be a list")
    require(isinstance(case["required_source_terms"], list), f"{case_id} required_source_terms must be a list")
    require(isinstance(case["min_sources"], int) and case["min_sources"] >= 0, f"{case_id} min_sources must be >= 0")
    require(isinstance(case["checks"], list) and case["checks"], f"{case_id} checks must be non-empty")

    unknown_checks = sorted(set(case["checks"]) - REQUIRED_CHECKS)
    require(not unknown_checks, f"{case_id} has unknown checks: {unknown_checks}")

    if case["category"] == "formula":
        combined = " ".join(case["expected_keywords"] + case["checks"])
        require("LaTeX" in combined or "does_not_invent_formula" in case["checks"], f"{case_id} must cover LaTeX policy")
    if case["category"] == "fallback":
        require(case["min_sources"] == 0, f"{case_id} fallback case should allow zero sources")
        require("safe_no_context_fallback" in case["checks"], f"{case_id} must check safe fallback")


def main() -> None:
    payload = load_eval()
    cases = payload.get("cases")
    require(isinstance(cases, list) and len(cases) >= 3, "RAG eval must include at least 3 cases")

    seen_ids: set[str] = set()
    for case in cases:
        require(isinstance(case, dict), "Each RAG eval case must be an object")
        validate_case(case, seen_ids)

    categories = {case["category"] for case in cases}
    for required_category in ["knowledge_summary", "formula", "fallback"]:
        require(required_category in categories, f"RAG eval missing category: {required_category}")

    print("RAG eval static harness passed.")


if __name__ == "__main__":
    main()
