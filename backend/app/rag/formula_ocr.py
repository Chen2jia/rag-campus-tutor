from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FormulaOcrResult:
    latex: str | None
    confidence: float
    status: str
    source: str = "formula_ocr"


DEFAULT_FORMULA_OCR_MIN_CONFIDENCE = 0.7


def build_formula_ocr_result(
    latex: str | None,
    confidence: float,
    min_confidence: float | None = None,
) -> FormulaOcrResult:
    # Callers can pass settings.formula_ocr_min_confidence when app config is available.
    threshold = DEFAULT_FORMULA_OCR_MIN_CONFIDENCE if min_confidence is None else min_confidence
    if not latex:
        return FormulaOcrResult(latex=None, confidence=confidence, status="failed")
    if confidence < threshold:
        return FormulaOcrResult(latex=None, confidence=confidence, status="low_confidence")
    return FormulaOcrResult(latex=latex, confidence=confidence, status="recognized")
