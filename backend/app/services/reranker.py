from sentence_transformers import CrossEncoder

_reranker = None

def get_reranker():
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    return _reranker


def rerank(query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
    """
    Re-rank candidates using a Cross-Encoder model.
    Takes the query and the candidate text (child_text or parent_text),
    scores them, and returns the top_k results.
    """
    if not candidates:
        return []

    reranker = get_reranker()

    # Build pairs of (query, candidate_text) for cross-encoder scoring
    pairs = []
    for c in candidates:
        text = c.get("parent_text", c.get("child_text", ""))
        pairs.append((query, text))

    scores = reranker.predict(pairs)

    # Attach scores and sort
    for i, c in enumerate(candidates):
        c["rerank_score"] = float(scores[i])

    ranked = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)
    return ranked[:top_k]
