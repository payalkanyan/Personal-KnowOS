from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import time

app = FastAPI(
    title="Personal Knowledge OS API",
    description="Backend API for Personal Knowledge OS Chrome Extension",
    version="1.0.0"
)

# Configure CORS for Extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Should be restricted in production
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
    print(f"\n[{time.strftime('%X')}] --- INGESTED NEW PAGE ---")
    print(f"Title: {payload.get('title')}")
    print(f"URL:   {payload.get('url')}")
    print(f"Stats: {payload.get('timeSpent')}s spent, {payload.get('scrollDepth')}% scrolled, {payload.get('wordCount')} words.")
    print("-" * 35 + "\n")
    
    return {
        "status": "accepted",
        "job_id": f"job_{int(time.time())}",
        "message": "Page sent to processing queue"
    }
