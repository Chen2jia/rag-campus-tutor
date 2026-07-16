from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_parser_module_exists() -> None:
    assert (ROOT / "app" / "rag" / "parser.py").exists()


def test_parser_defines_expected_data_structures() -> None:
    parser_text = (ROOT / "app" / "rag" / "parser.py").read_text(encoding="utf-8")
    for fragment in [
        "class TextBlock",
        "class ParsedPage",
        "class ParsedDocument",
        "page_number",
        "title_candidates",
    ]:
        assert fragment in parser_text


def test_parser_uses_pymupdf_dict_extraction() -> None:
    parser_text = (ROOT / "app" / "rag" / "parser.py").read_text(encoding="utf-8")
    assert "import_module(\"fitz\")" in parser_text
    assert "get_text(\"dict\")" in parser_text
    assert "_extract_text_blocks" in parser_text


def test_parser_title_heuristics_are_present() -> None:
    parser_text = (ROOT / "app" / "rag" / "parser.py").read_text(encoding="utf-8")
    for fragment in ["_is_likely_title", "body_font_size", "is_bold", "Chapter"]:
        assert fragment in parser_text
