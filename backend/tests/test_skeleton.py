from pathlib import Path


def test_expected_backend_skeleton_exists() -> None:
    root = Path(__file__).resolve().parents[1]
    expected_paths = [
        "app/main.py",
        "app/db.py",
        "app/core/config.py",
        "app/core/security.py",
        "app/core/deps.py",
        "app/routers/health.py",
        "app/routers/documents.py",
        "app/routers/tasks.py",
        "app/models/__init__.py",
        "app/schemas/__init__.py",
        "app/services/__init__.py",
        "app/agents/__init__.py",
        "app/rag/__init__.py",
        "requirements.txt",
        ".env.example",
    ]
    missing = [path for path in expected_paths if not (root / path).exists()]
    assert missing == []
