# Local Setup Guide: Personal Knowledge OS

This guide will walk you through spinning up the foundation of the Personal Knowledge OS locally, including the underlying databases, the FastAPI backend, and the Chrome extension.

---

## 1. Start up the Databases

The architecture relies on PostgreSQL, Qdrant, Neo4j, and Redis. We use Docker to host these locally without cluttering your system.

1. Ensure **Docker** is installed and running on your machine.
2. In the root of the project directory, execute the following command:
   ```bash
   docker compose up -d
   ```
   *(Note: Linux users might need to run `sudo docker compose up -d` depending on your docker group permissions).*

---

## 2. Spin up the FastAPI Backend

The backend server is responsible for receiving the data scraped by your browser, routing processing tasks, and performing retrievals. 

1. Open a terminal and navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Create and activate a fresh Python virtual environment:
   ```bash
   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   
   # On Windows
   
   python -m venv venv
   venv\Scripts\activate
   ```
3. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   *The server will boot up and will listen for requests at `http://localhost:8000`.*

---

## 3. Load the Chrome Extension

The extension acts as your ingestion layer. It injects a script into pages to monitor how long and deep you read, eventually collecting the site content if it meets your learning criteria.

1. Open Google Chrome.
2. Navigate to `chrome://extensions/` in your address bar.
3. Turn on **Developer mode** via the toggle switch in the top right corner.
4. Click the **Load unpacked** button in the top left.
5. In your file browser, select the `extension` folder located inside the root project directory.
6. The extension is now installed and active!

---

## 4. Verify the Pipeline

To make sure your ingestion pipeline is wired correctly end-to-end:

1. Keep the terminal that is running your FastAPI server visible on your screen.
2. Navigate to a text-heavy website (like a Wikipedia article).
3. Read on the page for **longer than 30 seconds**.
4. Scroll continuously until you've reached at least **40% depth** into the page.
5. Close the tab or navigate away.
6. Look at your FastAPI terminal. You should instantly see a confirmation log validating that the extension posted your site footprint successfully!
