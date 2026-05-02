from langchain_core.tools import tool
from app.services.vector_search import vector_search
from app.services.graph_search import graph_search
from app.services.fusion import reciprocal_rank_fusion
from app.services.reranker import rerank
from duckduckgo_search import DDGS

@tool
def search_personal_knowledge(query: str) -> str:
    """
    Search the user's personal knowledge base. Use this tool when the user asks about
    things they have saved, read, or stored previously.
    Returns synthesized context and source URLs from their database.
    """
    print(f"[Agent] Tool called: search_personal_knowledge -> {query}")
    try:
        v_res = vector_search(query, top_k=20)
    except Exception as e:
        print(f"[Agent] Vector search failed: {e}")
        v_res = []
        
    try:
        g_res = graph_search(query, top_k=10)
    except Exception as e:
        print(f"[Agent] Graph search failed: {e}")
        g_res = []
        
    if not v_res and not g_res:
        return "No information found in the personal knowledge base."
        
    fused = reciprocal_rank_fusion([v_res, g_res])
    top_cands = [c for c in fused if c.get("parent_text")][:20]
    
    if not top_cands:
        return "No valid context chunks found in the personal knowledge base."
        
    reranked = rerank(query, top_cands, top_k=5)
    
    seen = set()
    blocks = []
    for r in reranked:
        pid = r.get("parent_id", "")
        if pid and pid not in seen:
            seen.add(pid)
            # Pass source URL inline so the LLM can cite it
            blocks.append(f"Context: {r['parent_text']}\nSource URL: {r.get('url', '')}")
            
    if not blocks:
        return "No relevant information found in the personal knowledge base after re-ranking."
        
    return "\n\n---\n\n".join(blocks)

@tool
def search_live_web(query: str) -> str:
    """
    Search the live internet. Use this tool when the user asks about current events,
    recent news, or facts that are not likely to be in their personal knowledge base.
    """
    print(f"[Agent] Tool called: search_live_web -> {query}")
    try:
        results = list(DDGS().text(query, max_results=3))
        if not results:
             return "No results found on the web."
        return "\n".join([f"Snippet: {r.get('body', '')}\nSource URL: {r.get('href', '')}" for r in results])
    except Exception as e:
        print(f"[Agent] DDGS Exception: {e}")
        return f"Web search failed: {e}"
