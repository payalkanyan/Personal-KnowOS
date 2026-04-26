from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
from app.core.config import settings

qdrant = QdrantClient(url=settings.QDRANT_URL)
collection_name = "knowledge_chunks"

_model = None
def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    return _model


def vector_search(query: str, top_k: int = 20) -> list:
    """
    Embed the query and search Qdrant for the closest child chunks.
    Returns a list of dicts with score, child_text, parent_text, url, title.
    """
    model = get_model()
    query_vector = model.encode(query).tolist()

    results = qdrant.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=top_k,
        with_payload=True,
    )

    hits = []
    for r in results.points:
        hits.append({
            "score": r.score,
            "child_text": r.payload.get("child_text", ""),
            "parent_text": r.payload.get("parent_text", ""),
            "parent_id": r.payload.get("parent_id", ""),
            "url": r.payload.get("url", ""),
            "title": r.payload.get("title", ""),
        })
    return hits
