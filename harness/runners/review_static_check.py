from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    required_paths = [
        "backend/app/routers/review.py",
        "backend/app/services/review_service.py",
        "backend/app/schemas/review.py",
    ]
    missing = [path for path in required_paths if not (ROOT / path).exists()]
    if missing:
        raise SystemExit(f"Missing review API paths: {', '.join(missing)}")

    service_text = (ROOT / "backend" / "app" / "services" / "review_service.py").read_text(
        encoding="utf-8"
    )
    required_fragments = [
        "ReviewSchedule.user_id == user.id",
        "ReviewSchedule.next_review_date <= target_date",
        "_calculate_sm2",
        "Review item not found",
    ]
    missing_fragments = [fragment for fragment in required_fragments if fragment not in service_text]
    if missing_fragments:
        raise SystemExit(f"Review service missing fragments: {', '.join(missing_fragments)}")

    print("Review static harness passed.")


if __name__ == "__main__":
    main()
