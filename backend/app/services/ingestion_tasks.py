from app.core.celery_app import celery_app
from app.core.config import settings
import hashlib
import redis
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from app.services.entity_extractor import extract_and_store_entities

# Initialize DB connections
redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
qdrant = QdrantClient(url=settings.QDRANT_URL)
collection_name = "knowledge_chunks"

# Lazy-loaded embedding model placeholder
_model = None
def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    return _model

# Ensure collection exists
try:
    qdrant.get_collection(collection_name)
except Exception:
    qdrant.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )

def chunk_text(text: str, parent_words=600, child_words=150):
    words = text.split()
    chunks = []
    for i in range(0, len(words), parent_words):
        parent = " ".join(words[i:i+parent_words])
        parent_id = str(uuid.uuid4())
        
        # Generate smaller child chunks associated with this parent
        for j in range(0, len(parent.split()), child_words):
            child = " ".join(parent.split()[j:j+child_words])
            if child:
                chunks.append({
                    "parent_id": parent_id,
                    "parent_text": parent,
                    "child_id": str(uuid.uuid4()),
                    "child_text": child
                })
    return chunks

@celery_app.task(bind=True)
def process_page(self, payload: dict):
    title = payload.get('title', 'Unknown Title')
    url = payload.get('url', 'Unknown URL')
    content = payload.get('content', '')
    
    print(f"[Celery] Processing started: {title[:50]}...")
    
    if not content:
        return {"status": "error", "message": "Empty content"}

    # TASK 1: Deduplication
    fingerprint = hashlib.sha256(content.encode('utf-8')).hexdigest()
    if redis_client.get(f"doc:{fingerprint}"):
        print(f"[Celery] Found duplicate fingerprint {fingerprint}. Terminating.")
        return {"status": "skipped", "message": "Duplicate"}
    
    # TASK 2: Chunking Strategy
    print(f"[Celery] Document is new. Chunking payload...")
    pairs = chunk_text(content)
    
    # TASK 3: Generating Embeddings & Qdrant Upsert
    print(f"[Celery] Generating embeddings for {len(pairs)} child chunks...")
    model = get_model()
    
    points = []
    for pair in pairs:
        embedding = model.encode(pair["child_text"]).tolist()
        
        points.append(
            PointStruct(
                id=pair["child_id"],
                vector=embedding,
                payload={
                    "url": url,
                    "title": title,
                    "doc_fingerprint": fingerprint,
                    "child_text": pair["child_text"],
                    "parent_id": pair["parent_id"],
                    "parent_text": pair["parent_text"],
                }
            )
        )
    
    if points:
        qdrant.upsert(
            collection_name=collection_name,
            points=points
        )
        print(f"[Celery] Upserted {len(points)} vectors into Qdrant successfully!")

    # Cache document signature heavily downstream
    redis_client.setex(f"doc:{fingerprint}", 86400, "scraped")
    
    # TASK 4: Entity Extraction → Neo4j Knowledge Graph
    print(f"[Celery] Extracting entities for Neo4j...")
    try:
        entity_count = extract_and_store_entities(url, title, content, fingerprint)
    except Exception as e:
        print(f"[Celery] Neo4j entity extraction failed (non-fatal): {e}")
        entity_count = 0

    return {"status": "success", "chunks_upserted": len(points), "entities_extracted": entity_count}
