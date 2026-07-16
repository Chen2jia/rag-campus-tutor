from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "EduMate — Phase 10 PRD 验收报告.md"


def test_phase10_prd_acceptance_report_exists() -> None:
    assert REPORT.exists()


def test_phase10_prd_acceptance_report_covers_required_scope() -> None:
    report = REPORT.read_text(encoding="utf-8")
    for fragment in [
        "轻量用户注册",
        "JWT",
        "多用户数据隔离",
        "PDF 上传",
        "Qdrant",
        "BM25",
        "RRF",
        "RAG 问答",
        "MasterAgent",
        "KnowledgeAgent",
        "PlannerAgent",
        "SM-2",
        "Vue",
        "Docker Compose",
        "Harness",
    ]:
        assert fragment in report


def test_phase10_prd_acceptance_report_records_limits_and_next_iteration() -> None:
    report = REPORT.read_text(encoding="utf-8")
    for fragment in [
        "已知限制",
        "未配置 LLM/API key",
        "低置信度不生成 LaTeX",
        "E2E",
        "下一轮迭代建议",
        "v0.1.0-demo",
    ]:
        assert fragment in report
