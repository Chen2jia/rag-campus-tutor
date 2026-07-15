from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    required_paths = [
        "backend/app/routers/plan.py",
        "backend/app/agents/planner_agent.py",
        "backend/app/schemas/plan.py",
    ]
    missing = [path for path in required_paths if not (ROOT / path).exists()]
    if missing:
        raise SystemExit(f"Missing plan API paths: {', '.join(missing)}")

    agent_text = (ROOT / "backend" / "app" / "agents" / "planner_agent.py").read_text(
        encoding="utf-8"
    )
    required_fragments = [
        "TaskService",
        "create_task",
        "_build_placeholder_plan",
        "_format_plan_text",
    ]
    missing_fragments = [fragment for fragment in required_fragments if fragment not in agent_text]
    if missing_fragments:
        raise SystemExit(f"Planner agent missing fragments: {', '.join(missing_fragments)}")

    print("Plan static harness passed.")


if __name__ == "__main__":
    main()
