from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_rag_eval_files_exist() -> None:
    assert (ROOT / "harness" / "evals" / "rag_eval_cases.json").exists()
    assert (ROOT / "harness" / "runners" / "rag_eval_static_check.py").exists()
    assert (ROOT / "harness" / "runners" / "rag_eval.py").exists()
    assert (ROOT / "harness" / "scripts" / "check_rag_eval_static.ps1").exists()
    assert (ROOT / "harness" / "scripts" / "check_rag_eval.ps1").exists()


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


def test_rag_eval_runner_uploads_fixture_and_scores_cases() -> None:
    runner_text = (ROOT / "harness" / "runners" / "rag_eval.py").read_text(encoding="utf-8")
    for fragment in [
        "rag_eval_cases.json",
        "latest_rag_eval.json",
        "/api/auth/register",
        "/api/documents/upload",
        "/api/rag/ask",
        "sample_pdf_bytes",
        "wait_for_document",
        "score_case",
        "RAG_EVAL_STRICT",
        "answer_mentions_expected_keywords",
        "has_citation_source",
        "does_not_invent_formula",
        "safe_no_context_fallback",
    ]:
        assert fragment in runner_text


def test_rag_eval_script_propagates_python_exit_code() -> None:
    script_text = (ROOT / "harness" / "scripts" / "check_rag_eval.ps1").read_text(encoding="utf-8")
    assert "python harness/runners/rag_eval.py" in script_text
    assert "$LASTEXITCODE" in script_text
    assert "exit $LASTEXITCODE" in script_text
