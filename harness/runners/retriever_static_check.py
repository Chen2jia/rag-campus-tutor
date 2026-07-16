from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    required_paths = [
        "backend/app/rag/retriever.py",
    ]
    missing = [path for path in required_paths if not (ROOT / path).exists()]
    if missing:
        raise SystemExit(f"Missing retriever paths: {', '.join(missing)}")

    retriever_text = (ROOT / "backend" / "app" / "rag" / "retriever.py").read_text(
        encoding="utf-8"
    )
    required_fragments = [
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
        "VectorSearchHit",
        "Bm25Hit",
    ]
    missing_fragments = [fragment for fragment in required_fragments if fragment not in retriever_text]
    if missing_fragments:
        raise SystemExit(f"Retriever missing fragments: {', '.join(missing_fragments)}")

    print("Retriever static harness passed.")


if __name__ == "__main__":
    main()
