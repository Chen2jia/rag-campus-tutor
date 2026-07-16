from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.rag.formula_normalizer import looks_like_formula, normalize_formula_to_latex
from app.rag.formula_ocr import build_formula_ocr_result



def test_formula_modules_exist() -> None:
    assert (ROOT / "app" / "rag" / "formula_normalizer.py").exists()
    assert (ROOT / "app" / "rag" / "formula_ocr.py").exists()


def test_native_formula_normalization_replaces_common_symbols() -> None:
    latex = normalize_formula_to_latex("α + β ≤ γ")
    assert r"\alpha" in latex
    assert r"\beta" in latex
    assert r"\le" in latex
    assert r"\gamma" in latex


def test_formula_detection_recognizes_math_lines() -> None:
    assert looks_like_formula("E = mc²")
    assert looks_like_formula("lim x → 0")
    assert not looks_like_formula("This is a normal paragraph about calculus history.")


def test_ocr_low_confidence_drops_latex() -> None:
    result = build_formula_ocr_result(latex=r"E=mc^2", confidence=0.69, min_confidence=0.7)
    assert result.status == "low_confidence"
    assert result.latex is None


def test_ocr_high_confidence_keeps_latex() -> None:
    result = build_formula_ocr_result(latex=r"E=mc^2", confidence=0.71, min_confidence=0.7)
    assert result.status == "recognized"
    assert result.latex == r"E=mc^2"
