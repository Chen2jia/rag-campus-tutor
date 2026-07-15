from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    required_paths = [
        "backend/app/routers/tasks.py",
        "backend/app/services/task_service.py",
        "backend/app/schemas/task.py",
    ]
    missing = [path for path in required_paths if not (ROOT / path).exists()]
    if missing:
        raise SystemExit(f"Missing task API paths: {', '.join(missing)}")

    service_text = (ROOT / "backend" / "app" / "services" / "task_service.py").read_text(
        encoding="utf-8"
    )
    required_fragments = [
        "Task.user_id == user.id",
        "Task.is_done == is_done",
        "Task.due_date == due_date",
        "Task not found",
    ]
    missing_fragments = [fragment for fragment in required_fragments if fragment not in service_text]
    if missing_fragments:
        raise SystemExit(f"Task service missing fragments: {', '.join(missing_fragments)}")

    print("Tasks static harness passed.")


if __name__ == "__main__":
    main()
