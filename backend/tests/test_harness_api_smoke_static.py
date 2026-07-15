from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_api_smoke_harness_exists() -> None:
    assert (ROOT / "harness" / "runners" / "api_smoke.py").exists()
    assert (ROOT / "harness" / "scripts" / "check_api_smoke.ps1").exists()


def test_api_smoke_targets_auth_flow() -> None:
    text = (ROOT / "harness" / "runners" / "api_smoke.py").read_text(encoding="utf-8")
    for endpoint in [
        "/api/health",
        "/api/auth/me",
        "/api/auth/register",
        "/api/auth/login",
    ]:
        assert endpoint in text
    assert "latest_auth_smoke.json" in text
