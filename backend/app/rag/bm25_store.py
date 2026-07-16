from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from math import log


@dataclass(frozen=True)
class Bm25Hit:
    key: str
    score: float
    text: str


class Bm25Store:
    """Thin BM25 wrapper with a safe fallback when rank_bm25 is unavailable."""

    def __init__(self, corpus: list[str] | None = None) -> None:
        self.corpus = corpus or []

    def search(self, query: str, documents: list[tuple[str, str]], limit: int = 10) -> list[Bm25Hit]:
        clean_query = self._normalize(query)
        if not clean_query or not documents:
            return []

        tokens = self._tokenize(clean_query)
        if not tokens:
            return []

        try:
            return self._search_with_rank_bm25(tokens=tokens, documents=documents, limit=limit)
        except ModuleNotFoundError:
            return self._search_with_fallback(tokens=tokens, documents=documents, limit=limit)

    def _search_with_rank_bm25(
        self,
        tokens: list[str],
        documents: list[tuple[str, str]],
        limit: int,
    ) -> list[Bm25Hit]:
        bm25_module = import_module("rank_bm25")
        model = bm25_module.BM25Okapi([self._tokenize(text) for _, text in documents])
        scores = model.get_scores(tokens)
        hits = [
            Bm25Hit(key=key, score=float(score), text=text)
            for (key, text), score in zip(documents, scores, strict=False)
        ]
        return sorted(hits, key=lambda item: item.score, reverse=True)[:limit]

    def _search_with_fallback(
        self,
        tokens: list[str],
        documents: list[tuple[str, str]],
        limit: int,
    ) -> list[Bm25Hit]:
        token_set = set(tokens)
        hits: list[Bm25Hit] = []
        for key, text in documents:
            doc_tokens = self._tokenize(text)
            if not doc_tokens:
                continue
            overlap = len(token_set.intersection(doc_tokens))
            if overlap == 0:
                continue
            score = overlap / (len(doc_tokens) ** 0.5)
            hits.append(Bm25Hit(key=key, score=score, text=text))
        return sorted(hits, key=lambda item: item.score, reverse=True)[:limit]

    @staticmethod
    def _normalize(text: str) -> str:
        return " ".join(text.split()).strip()

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        normalized = Bm25Store._normalize(text).lower()
        if not normalized:
            return []
        tokens: list[str] = []
        current: list[str] = []
        for char in normalized:
            if char.isalnum() or char in {"_", "-"}:
                current.append(char)
            elif current:
                tokens.append("".join(current))
                current = []
        if current:
            tokens.append("".join(current))
        return tokens

    @staticmethod
    def idf(term_frequency: int, document_count: int) -> float:
        return log((document_count - term_frequency + 0.5) / (term_frequency + 0.5) + 1.0)
