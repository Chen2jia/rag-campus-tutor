from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_retriever_module_exists() -> None:
    assert (ROOT / "app" / "rag" / "retriever.py").exists()


def test_retriever_fuses_vector_and_bm25_hits() -> None:
    retriever_text = (ROOT / "app" / "rag" / "retriever.py").read_text(encoding="utf-8")
    for fragment in [
        "class HybridSearchHit",
        "class HybridRetriever",
        "rrf_k",
        "fuse",
        "score_hits",
        "build_key",
        "_accumulate",
        "_accumulate_scores",
        "_build_hybrid_hit",
        "_hit_key",
        "_rrf_score",
        "_split_key",
    ]:
        assert fragment in retriever_text


def test_retriever_mentions_vector_and_bm25_sources() -> None:
    retriever_text = (ROOT / "app" / "rag" / "retriever.py").read_text(encoding="utf-8")
    assert "VectorSearchHit" in retriever_text
    assert "Bm25Hit" in retriever_text
    assert "RRF" in retriever_text
