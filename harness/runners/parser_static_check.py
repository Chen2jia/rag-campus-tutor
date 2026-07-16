from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser_path = ROOT / "backend" / "app" / "rag" / "parser.py"
    if not parser_path.exists():
        raise SystemExit("Missing parser module: backend/app/rag/parser.py")

    parser_text = parser_path.read_text(encoding="utf-8")
    required_fragments = [
        "class FormulaInfo",
        "class TextBlock",
        "class ParsedPage",
        "class ParsedDocument",
        "def parse_pdf",
        "get_text(\"dict\")",
        "title_candidates",
        "formula_blocks",
        "block_type",
        "normalize_formula_to_latex",
        "_is_likely_title",
        "_is_formula_candidate",
        "import_module(\"fitz\")",
    ]
    missing = [fragment for fragment in required_fragments if fragment not in parser_text]
    if missing:
        raise SystemExit(f"Parser module missing fragments: {', '.join(missing)}")

    print("Parser static harness passed.")


if __name__ == "__main__":
    main()
