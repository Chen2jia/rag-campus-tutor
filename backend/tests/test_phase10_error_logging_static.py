from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_phase10_error_handler_infrastructure_exists() -> None:
    expected = [
        "app/core/errors.py",
        "app/core/logging.py",
    ]
    missing = [path for path in expected if not (ROOT / path).exists()]
    assert missing == []


def test_phase10_app_registers_error_handlers_and_request_logging() -> None:
    main_text = read("app/main.py")
    for fragment in [
        "configure_logging()",
        "register_error_handlers(app)",
        '@app.middleware("http")',
        "X-Request-ID",
        "request_completed",
        "duration_ms",
        "request_failed",
    ]:
        assert fragment in main_text


def test_phase10_error_responses_keep_detail_and_request_id() -> None:
    errors_text = read("app/core/errors.py")
    for fragment in [
        "http_exception_handler",
        "validation_exception_handler",
        "unhandled_exception_handler",
        '"detail": detail',
        '"error": {',
        '"request_id": request_id',
        '"X-Request-ID": request_id',
        '"validation_error"',
        '"internal_error"',
        "settings.app_env != \"production\"",
    ]:
        assert fragment in errors_text


def test_phase10_logging_level_is_env_configurable() -> None:
    config_text = read("app/core/config.py")
    env_text = read(".env.example")
    logging_text = read("app/core/logging.py")

    assert 'log_level: str = "INFO"' in config_text
    assert "LOG_LEVEL=INFO" in env_text
    assert "settings.log_level.upper()" in logging_text
    assert "logging.basicConfig" in logging_text
