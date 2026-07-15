from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_phase2_auth_files_exist() -> None:
    expected_paths = [
        "app/models/user.py",
        "app/models/document.py",
        "app/models/task.py",
        "app/models/review.py",
        "app/schemas/auth.py",
        "app/services/auth_service.py",
        "app/routers/auth.py",
        "alembic.ini",
        "alembic/env.py",
        "alembic/versions/202607160001_create_auth_and_learning_tables.py",
    ]
    missing = [path for path in expected_paths if not (ROOT / path).exists()]
    assert missing == []


def test_business_models_include_user_id() -> None:
    for model_file in ["document.py", "task.py", "review.py"]:
        text = (ROOT / "app" / "models" / model_file).read_text(encoding="utf-8")
        assert "user_id" in text
        assert 'ForeignKey("users.id", ondelete="CASCADE")' in text


def test_auth_router_is_registered() -> None:
    main_text = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
    assert "auth" in main_text
    assert "app.include_router(auth.router" in main_text


def test_migration_creates_required_tables() -> None:
    migration_text = (
        ROOT / "alembic" / "versions" / "202607160001_create_auth_and_learning_tables.py"
    ).read_text(encoding="utf-8")
    for table_name in ["users", "documents", "tasks", "review_schedule"]:
        assert f'"{table_name}"' in migration_text
    assert "user_id" in migration_text
