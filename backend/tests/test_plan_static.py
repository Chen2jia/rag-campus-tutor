from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_plan_api_files_exist() -> None:
    expected = [
        "app/routers/plan.py",
        "app/agents/planner_agent.py",
        "app/schemas/plan.py",
    ]
    missing = [path for path in expected if not (ROOT / path).exists()]
    assert missing == []


def test_plan_router_is_registered() -> None:
    main_text = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
    assert "plan" in main_text
    assert "app.include_router(plan.router" in main_text


def test_plan_route_matches_prd_surface() -> None:
    router_text = (ROOT / "app" / "routers" / "plan.py").read_text(encoding="utf-8")
    assert '@router.post("/generate"' in router_text
    assert "PlannerAgent" in router_text


def test_planner_agent_creates_tasks() -> None:
    agent_text = (ROOT / "app" / "agents" / "planner_agent.py").read_text(encoding="utf-8")
    for fragment in [
        "TaskService",
        "create_task",
        "TaskCreate",
        "created_tasks",
        "_build_placeholder_plan",
        "_format_plan_text",
    ]:
        assert fragment in agent_text


def test_plan_schema_contains_expected_fields() -> None:
    schema_text = (ROOT / "app" / "schemas" / "plan.py").read_text(encoding="utf-8")
    for fragment in ["goal", "days", "subject", "start_date", "plan_text", "created_tasks"]:
        assert fragment in schema_text
