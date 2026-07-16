from __future__ import annotations

import re


GREEK_SYMBOLS = {
    "α": r"\alpha",
    "β": r"\beta",
    "γ": r"\gamma",
    "δ": r"\delta",
    "ε": r"\epsilon",
    "θ": r"\theta",
    "λ": r"\lambda",
    "μ": r"\mu",
    "π": r"\pi",
    "ρ": r"\rho",
    "σ": r"\sigma",
    "τ": r"\tau",
    "φ": r"\phi",
    "ω": r"\omega",
    "Γ": r"\Gamma",
    "Δ": r"\Delta",
    "Θ": r"\Theta",
    "Λ": r"\Lambda",
    "Π": r"\Pi",
    "Σ": r"\Sigma",
    "Φ": r"\Phi",
    "Ω": r"\Omega",
}

MATH_SYMBOLS = {
    "≤": r"\le",
    "≥": r"\ge",
    "≠": r"\ne",
    "≈": r"\approx",
    "∞": r"\infty",
    "∑": r"\sum",
    "∏": r"\prod",
    "∫": r"\int",
    "√": r"\sqrt",
    "∂": r"\partial",
    "∇": r"\nabla",
    "→": r"\to",
    "⇒": r"\Rightarrow",
    "∈": r"\in",
    "∉": r"\notin",
    "⊂": r"\subset",
    "⊆": r"\subseteq",
    "∪": r"\cup",
    "∩": r"\cap",
    "×": r"\times",
    "÷": r"\div",
    "±": r"\pm",
}

SUPERSCRIPTS = {
    "⁰": "0",
    "¹": "1",
    "²": "2",
    "³": "3",
    "⁴": "4",
    "⁵": "5",
    "⁶": "6",
    "⁷": "7",
    "⁸": "8",
    "⁹": "9",
    "ⁿ": "n",
}

SUBSCRIPTS = {
    "₀": "0",
    "₁": "1",
    "₂": "2",
    "₃": "3",
    "₄": "4",
    "₅": "5",
    "₆": "6",
    "₇": "7",
    "₈": "8",
    "₉": "9",
}

LATEX_FUNCTIONS = {
    "argmax": r"\arg\max",
    "argmin": r"\arg\min",
    "lim": r"\lim",
    "log": r"\log",
    "ln": r"\ln",
    "sin": r"\sin",
    "cos": r"\cos",
    "tan": r"\tan",
    "max": r"\max",
    "min": r"\min",
}

FORMULA_KEYWORDS = set(LATEX_FUNCTIONS)
FORMULA_SYMBOLS = set("=+-*/^_()[]{}|<>") | set(GREEK_SYMBOLS) | set(MATH_SYMBOLS)


def looks_like_formula(text: str) -> bool:
    clean_text = text.strip()
    if not clean_text:
        return False

    math_symbol_count = sum(1 for char in clean_text if char in FORMULA_SYMBOLS)
    digit_count = sum(1 for char in clean_text if char.isdigit())
    keyword_hit = any(re.search(rf"\b{keyword}\b", clean_text, re.IGNORECASE) for keyword in FORMULA_KEYWORDS)
    has_equation_number = bool(re.search(r"\(\s*\d+(\.\d+)?\s*\)$", clean_text))
    density = (math_symbol_count + digit_count) / max(len(clean_text), 1)

    special_math_chars = set(GREEK_SYMBOLS) | set(MATH_SYMBOLS)
    return (
        "=" in clean_text
        or keyword_hit
        or has_equation_number
        or any(char in clean_text for char in special_math_chars)
        or (len(clean_text) <= 100 and density >= 0.18 and math_symbol_count >= 2)
    )


def normalize_formula_to_latex(text: str) -> str:
    latex = text.strip()
    latex = _replace_words(latex)
    latex = _replace_chars(latex, GREEK_SYMBOLS)
    latex = _replace_chars(latex, MATH_SYMBOLS)
    latex = _replace_super_sub_scripts(latex)
    latex = _normalize_sqrt(latex)
    latex = _normalize_common_indices(latex)
    latex = re.sub(r"\s+", " ", latex).strip()
    return latex


def _replace_words(text: str) -> str:
    result = text
    for word, latex in sorted(LATEX_FUNCTIONS.items(), key=lambda item: len(item[0]), reverse=True):
        result = re.sub(rf"\b{word}\b", lambda _: latex, result, flags=re.IGNORECASE)
    return result


def _replace_chars(text: str, mapping: dict[str, str]) -> str:
    result = text
    for source, target in mapping.items():
        result = result.replace(source, f" {target} ")
    return result


def _replace_super_sub_scripts(text: str) -> str:
    result = ""
    for char in text:
        if char in SUPERSCRIPTS:
            result += f"^{{{SUPERSCRIPTS[char]}}}"
        elif char in SUBSCRIPTS:
            result += f"_{{{SUBSCRIPTS[char]}}}"
        else:
            result += char
    return result


def _normalize_sqrt(text: str) -> str:
    return re.sub(r"\\sqrt\s+([A-Za-z0-9]+)", r"\\sqrt{\1}", text)


def _normalize_common_indices(text: str) -> str:
    text = re.sub(r"\b([A-Za-z])_(\d+|[A-Za-z])\b", r"\1_{\2}", text)
    text = re.sub(r"\b([A-Za-z])\^(\d+|[A-Za-z])\b", r"\1^{\2}", text)
    return text
