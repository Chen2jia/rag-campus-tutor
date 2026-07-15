from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_review_api_files_exist() -> None:
    expected = [
        "app/routers/review.py",
        "app/services/review_service.py",
        "app/schemas/review.py",
    ]
    missing = [path for path in expected if not (ROOT / path).exists()]
    assert missing == []


def test_review_router_is_registered() -> None:
    main_text = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
    assert "review" in main_text
    assert "app.include_router(review.router" in main_text


def test_review_routes_match_prd_surface() -> None:
    router_text = (ROOT / "app" / "routers" / "review.py").read_text(encoding="utf-8")
    for route_fragment in [
        '@router.post("",',
        '@router.get("/today"',
        '@router.put("/{review_id}/rate"',
    ]:
        assert route_fragment in router_text


def test_review_service_filters_by_current_user() -> None:
    service_text = (ROOT / "app" / "services" / "review_service.py").read_text(encoding="utf-8")
    assert "ReviewSchedule.user_id == user.id" in service_text
    assert "ReviewSchedule.id == review_id" in service_text


def test_review_service_supports_today_and_sm2() -> None:
    service_text = (ROOT / "app" / "services" / "review_service.py").read_text(encoding="utf-8")
    for fragment in [
        "ReviewSchedule.next_review_date <= target_date",
        "_calculate_sm2",
        "score < 3",
        "ease_factor",
        "interval_days",
        "next_review_date",
    ]:
        assert fragment in service_text
