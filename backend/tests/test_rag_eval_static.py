from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_rag_eval_files_exist() -> None:
    assert (ROOT / "harness" / "evals" / "rag_eval_cases.json").exists()
    assert (ROOT / "harness" / "runners" / "rag_eval_static_check.py").exists()
    assert (ROOT / "harness" / "scripts" / "check_rag_eval_static.ps1").exists()


def test_rag_eval_static_runner_validates_required_categories_and_checks() -> None:
    runner_text = (ROOT / "harness" / "runners" / "rag_eval_static_check.py").read_text(
        encoding="utf-8"
    )
    for fragment in [
        "rag_eval_cases.json",
        "answer_mentions_expected_keywords",
        "has_citation_source",
        "does_not_invent_formula",
        "safe_no_context_fallback",
        "knowledge_summary",
        "formula",
        "fallback",
        "RAG eval static harness passed.",
    ]:
        assert fragment in runner_text


def test_rag_eval_dataset_covers_summary_formula_and_fallback() -> None:
    eval_text = (ROOT / "harness" / "evals" / "rag_eval_cases.json").read_text(encoding="utf-8")
    for fragment in [
        "rag_calculus_taylor_summary",
        "rag_formula_latex_policy",
        "rag_no_context_fallback",
        "Taylor",
        "LaTeX",
        "does_not_invent_formula",
        "safe_no_context_fallback",
    ]:
        assert fragment in eval_text
