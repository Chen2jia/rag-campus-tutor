from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    required_paths = [
        "backend/app/rag/formula_normalizer.py",
        "backend/app/rag/formula_ocr.py",
    ]
    missing = [path for path in required_paths if not (ROOT / path).exists()]
    if missing:
        raise SystemExit(f"Missing formula modules: {', '.join(missing)}")

    normalizer_text = (ROOT / "backend" / "app" / "rag" / "formula_normalizer.py").read_text(
        encoding="utf-8"
    )
    ocr_text = (ROOT / "backend" / "app" / "rag" / "formula_ocr.py").read_text(encoding="utf-8")
    required_normalizer_fragments = [
        "GREEK_SYMBOLS",
        "MATH_SYMBOLS",
        "looks_like_formula",
        "normalize_formula_to_latex",
    ]
    required_ocr_fragments = [
        "FormulaOcrResult",
        "formula_ocr_min_confidence",
        "low_confidence",
        "latex=None",
    ]
    missing_fragments = [
        fragment for fragment in required_normalizer_fragments if fragment not in normalizer_text
    ] + [fragment for fragment in required_ocr_fragments if fragment not in ocr_text]
    if missing_fragments:
        raise SystemExit(f"Formula modules missing fragments: {', '.join(missing_fragments)}")

    print("Formula static harness passed.")


if __name__ == "__main__":
    main()
