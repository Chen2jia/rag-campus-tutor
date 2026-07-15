from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_task_api_files_exist() -> None:
    expected = [
        "app/routers/tasks.py",
        "app/services/task_service.py",
        "app/schemas/task.py",
    ]
    missing = [path for path in expected if not (ROOT / path).exists()]
    assert missing == []


def test_task_router_is_registered() -> None:
    main_text = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
    assert "tasks" in main_text
    assert "app.include_router(tasks.router" in main_text


def test_task_routes_match_prd_surface() -> None:
    router_text = (ROOT / "app" / "routers" / "tasks.py").read_text(encoding="utf-8")
    for route_fragment in [
        '@router.get("",',
        '@router.post("",',
        '@router.put("/{task_id}"',
        '@router.delete("/{task_id}"',
    ]:
        assert route_fragment in router_text


def test_task_service_filters_by_current_user() -> None:
    service_text = (ROOT / "app" / "services" / "task_service.py").read_text(encoding="utf-8")
    assert "Task.user_id == user.id" in service_text
    assert "select(Task).where(Task.id == task_id, Task.user_id == user.id)" in service_text


def test_task_service_supports_filters_and_updates() -> None:
    service_text = (ROOT / "app" / "services" / "task_service.py").read_text(encoding="utf-8")
    for fragment in [
        "Task.is_done == is_done",
        "Task.due_date == due_date",
        "task.title",
        "task.subject",
        "task.priority",
        "task.due_date",
        "task.is_done",
    ]:
        assert fragment in service_text
