import traceback
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import re

from app.services.ingestion_tasks import process_page
from app.services.agent import agent_executor
from langchain_core.messages import HumanMessage, SystemMessage
from app.core.config import settings

app = FastAPI(
    title="Personal Knowledge OS API",
    description="Agentic endpoint for ingestion and retrieval.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/v1/ingest")
async def ingest_url(request: Request):
    """
    Ingest a URL asynchronously via Celery.
    """
    try:
        payload = await request.json()

        if not payload.get("url") or not payload.get("content"):
            return JSONResponse(
                status_code=400,
                content={"error": "Missing url or content"}
            )
        
        # Dispatch Celery task
        task = process_page.delay(payload)
        
        return {"status": "accepted", "task_id": str(task.id)}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.post("/api/v1/query")
async def query_knowledge(request: Request):
    """
    Agentic Query Endpoint using LangGraph.
    The Agent autonomously decides whether to search the personal knowledge base or the live web.
    """
    try:
        body = await request.json()
        query = body.get("query")
        
        if not query:
            return JSONResponse(status_code=400, content={"error": "Missing query"})

        print(f"[Agent] Invoking LangGraph for: {query}")
        
        system_prompt = """You are a highly capable Personal Knowledge Assistant.
        You have access to the user's personal knowledge base, as well as the live internet.
        When the user asks a question:
        1. Always try to answer using the `search_personal_knowledge` tool first.
        2. If the user asks about current events or things clearly not in their database, use `search_live_web`.
        3. You may use both tools to compare information.
        4. ALWAYS cite the source URLs you retrieve from the tools at the bottom of your answer.
        """
        
        inputs = {"messages": [
            SystemMessage(content=system_prompt),
            HumanMessage(content=query)
        ]}
        
        # Run the agent graph
        result = agent_executor.invoke(inputs)
        
        # The final message is the last one in the state
        final_answer = result["messages"][-1].content
        
        if isinstance(final_answer, list):
            text_parts = [part.get("text", "") for part in final_answer if isinstance(part, dict) and "text" in part]
            final_answer = "\n".join(text_parts)
        elif not isinstance(final_answer, str):
            final_answer = str(final_answer)
        
        # Extract URLs from the answer to pass back to the UI nicely
        urls = re.findall(r'(https?://[^\s)\]]+)', final_answer)
        sources = [{"url": url, "title": "Agent Cited Source", "relevance": "N/A"} for url in set(urls)]
        
        return {
            "query": query,
            "answer": final_answer,
            "context": "Context was fetched autonomously via Agent tools.",
            "sources": sources,
            "total_chunks_searched": -1,
            "graph_hits": -1,
            "final_results": len(sources),
        }
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})
