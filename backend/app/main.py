from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.services.ingestion_tasks import process_page
from app.services.vector_search import vector_search
from app.services.graph_search import graph_search
from app.services.fusion import reciprocal_rank_fusion
from app.services.reranker import rerank

app = FastAPI(
    title="Personal Knowledge OS API",
    description="Backend API for Personal Knowledge OS Chrome Extension",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "healthy", "service": "Personal Knowledge OS"}

@app.post("/api/v1/ingest")
async def ingest_page(request: Request):
    payload = await request.json()

    # Send payload to Celery background worker
    task = process_page.delay(payload)
    
    return {
        "status": "accepted",
        "job_id": task.id,
        "message": "Page sent to processing queue"
    }

@app.post("/api/v1/query")
async def query_knowledge(request: Request):
    import traceback
    try:
        body = await request.json()
        query = body.get("query", "")
        top_k = body.get("top_k", 5)

        if not query:
            return {"error": "Query cannot be empty"}

        # Step 1: Parallel retrieval — Vector search + Graph search
        print(f"[Query] Starting vector search for: {query}")
        vector_results = vector_search(query, top_k=20)
        print(f"[Query] Vector search returned {len(vector_results)} results")
        
        try:
            graph_results = graph_search(query, top_k=10)
            print(f"[Query] Graph search returned {len(graph_results)} results")
        except Exception as e:
            print(f"[Query] Graph search failed (non-fatal): {e}")
            graph_results = []

        # Step 2: Reciprocal Rank Fusion to merge both result sets
        fused = reciprocal_rank_fusion([vector_results, graph_results])
        print(f"[Query] RRF fused into {len(fused)} results")

        # Step 3: Cross-Encoder Re-ranking on top candidates
        top_candidates = [c for c in fused if c.get("parent_text")][:20]
        
        if top_candidates:
            reranked = rerank(query, top_candidates, top_k=top_k)
        else:
            reranked = []
        print(f"[Query] Re-ranked to {len(reranked)} results")

        # Step 4: Assemble context from parent chunks (parent-child retrieval)
        seen_parents = set()
        context_blocks = []
        sources = []

        for result in reranked:
            pid = result.get("parent_id", "")
            if pid and pid not in seen_parents:
                seen_parents.add(pid)
                context_blocks.append(result["parent_text"])
                sources.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "relevance": round(result.get("rerank_score", 0), 4)
                })

        assembled_context = "\n\n---\n\n".join(context_blocks)

        return {
            "query": query,
            "context": assembled_context,
            "sources": sources,
            "total_chunks_searched": len(vector_results),
            "graph_hits": len(graph_results),
            "final_results": len(reranked),
        }
    except Exception as e:
        traceback.print_exc()
        return {"error": str(e)}
