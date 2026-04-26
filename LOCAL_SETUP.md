# Local Setup Guide: Personal Knowledge OS

This guide walks you through running the full Personal Knowledge OS stack locally.

---

## Prerequisites

- **Docker** installed and running
- **Python 3.10+** installed
- **Google Chrome** browser

---

## 1. Start the Databases

```bash
# From project root
sudo docker compose up -d
```

This spins up:
- **PostgreSQL** on port `5432`
- **Qdrant** on port `6333`
- **Neo4j** on port `7474` (browser) / `7687` (bolt)
- **Redis** on port `6379`

---

## 2. Set up the Backend

```bash
cd backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate   # Linux/Mac
# venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt

# Download the spaCy English model
python -m spacy download en_core_web_sm
```

---

## 3. Start the FastAPI Server

```bash
# From backend/ directory, with venv activated
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Verify it's running: open `http://localhost:8000` in your browser — you should see `{"status":"healthy"}`.

---

## 4. Start the Celery Worker

Open a **second terminal** tab:

```bash
cd backend
source venv/bin/activate
celery -A app.core.celery_app worker --loglevel=info
```

This worker processes ingested pages in the background (chunking, embedding, entity extraction).

---

## 5. Load the Chrome Extension

1. Open Chrome and navigate to `chrome://extensions/`
2. Toggle **Developer mode** ON (top right)
3. Click **Load unpacked**
4. Select the `extension/` folder from the project root

---

## 6. Test the Full Pipeline

### Ingestion Test
1. Navigate to any long article (e.g. a Wikipedia page)
2. Click the extension icon → **Force Save Current Page**
3. Watch the Celery terminal for processing logs

### Query Test
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What did I read about Linux?", "top_k": 5}'
```

The response will contain:
- `context` — assembled parent chunks relevant to your query
- `sources` — URLs and titles of source pages
- Retrieval statistics

---

## Stopping Everything

```bash
# Stop Docker containers
sudo docker compose down

# Stop Celery worker
# Press Ctrl+C in the Celery terminal

# Stop FastAPI server
# Press Ctrl+C in the uvicorn terminal
```
