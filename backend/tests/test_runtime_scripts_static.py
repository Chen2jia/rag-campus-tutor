from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_runtime_scripts_exist() -> None:
    expected = [
        "backend/scripts/migrate.ps1",
        "backend/scripts/run_dev.ps1",
        "harness/scripts/start_infra.ps1",
        "harness/scripts/run_auth_flow.ps1",
        "harness/scripts/run_e2e_flow.ps1",
    ]
    missing = [path for path in expected if not (ROOT / path).exists()]
    assert missing == []


def test_backend_dockerfile_includes_migrations() -> None:
    dockerfile = (ROOT / "backend" / "Dockerfile").read_text(encoding="utf-8")
    assert "COPY alembic ./alembic" in dockerfile
    assert "COPY alembic.ini ." in dockerfile


def test_backend_requirements_pin_passlib_compatible_bcrypt() -> None:
    requirements = (ROOT / "backend" / "requirements.txt").read_text(encoding="utf-8")
    assert "passlib[bcrypt]==1.7.4" in requirements
    assert "bcrypt==4.0.1" in requirements


def test_compose_has_migrate_service_and_container_defaults() -> None:
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    assert "migrate:" in compose
    assert "alembic" in compose
    assert "DATABASE_URL" in compose
    assert "OPENAI_BASE_URL" in compose
    assert "LOG_LEVEL" in compose
    assert "postgresql+asyncpg://postgres:postgres@postgres:5432/edumate" in compose
