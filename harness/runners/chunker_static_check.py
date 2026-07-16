from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    chunker_path = ROOT / "backend" / "app" / "rag" / "chunker.py"
    if not chunker_path.exists():
        raise SystemExit("Missing chunker module: backend/app/rag/chunker.py")

    chunker_text = chunker_path.read_text(encoding="utf-8")
    required_fragments = [
        "class DocumentChunk",
        "def chunk_document",
        "page_start",
        "page_end",
        "contains_formula",
        "formulas",
        "[公式]",
        "_update_path",
        "_ends_with_formula",
    ]
    missing = [fragment for fragment in required_fragments if fragment not in chunker_text]
    if missing:
        raise SystemExit(f"Chunker module missing fragments: {', '.join(missing)}")

    print("Chunker static harness passed.")


if __name__ == "__main__":
    main()
