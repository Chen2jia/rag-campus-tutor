from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    required_paths = [
        "backend/app/routers/auth.py",
        "backend/app/services/auth_service.py",
        "backend/app/schemas/auth.py",
        "backend/app/models/user.py",
        "backend/alembic/versions/202607160001_create_auth_and_learning_tables.py",
    ]
    missing = [path for path in required_paths if not (ROOT / path).exists()]
    if missing:
        raise SystemExit(f"Missing auth harness paths: {', '.join(missing)}")
    print("Auth static harness passed.")


if __name__ == "__main__":
    main()
