from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    required_paths = [
        "backend/app/routers/documents.py",
        "backend/app/services/document_service.py",
        "backend/app/schemas/document.py",
    ]
    missing = [path for path in required_paths if not (ROOT / path).exists()]
    if missing:
        raise SystemExit(f"Missing document API paths: {', '.join(missing)}")

    service_text = (ROOT / "backend" / "app" / "services" / "document_service.py").read_text(
        encoding="utf-8"
    )
    required_fragments = [
        "Document.user_id == user.id",
        "Only PDF files are supported",
        "max_upload_bytes",
        "PDF file exceeds the 50MB limit",
    ]
    missing_fragments = [fragment for fragment in required_fragments if fragment not in service_text]
    if missing_fragments:
        raise SystemExit(f"Document service missing fragments: {', '.join(missing_fragments)}")

    print("Documents static harness passed.")


if __name__ == "__main__":
    main()
