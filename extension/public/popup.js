// Force Save functionality
document.getElementById('saveBtn').addEventListener('click', async () => {
    try {
        const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
        chrome.tabs.sendMessage(tab.id, {type: 'FORCE_SAVE'});
        document.getElementById('saveBtn').innerText = "Sent!";
    } catch (e) {
        console.error(e);
        document.getElementById('saveBtn').innerText = "Failed (Reload tab)";
    }
    setTimeout(() => {
        document.getElementById('saveBtn').innerText = "Force Save Current Page";
    }, 2000);
});

// Search functionality
document.getElementById('searchBtn').addEventListener('click', async () => {
    const queryInput = document.getElementById('queryInput');
    const searchBtn = document.getElementById('searchBtn');
    const resultsArea = document.getElementById('resultsArea');
    const query = queryInput.value.trim();

    if (!query) return;

    searchBtn.disabled = true;
    searchBtn.innerText = "Searching & Thinking...";
    resultsArea.innerHTML = "<em>Connecting to brain...</em>";

    try {
        const response = await fetch('http://localhost:8000/api/v1/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query, top_k: 3 })
        });

        if (!response.ok) throw new Error("Server Error");

        const data = await response.json();
        
        if (data.error) {
            resultsArea.innerHTML = `<span style="color:red">Error: ${data.error}</span>`;
            return;
        }

        // Render Answer
        let html = `<p><strong>Answer:</strong><br/> ${data.answer.replace(/\n/g, '<br>')}</p>`;
        
        // Render Sources
        if (data.sources && data.sources.length > 0) {
            html += `<hr><p><strong>Sources:</strong></p>`;
            data.sources.forEach((s, i) => {
                html += `<a class="source-link" href="${s.url}" target="_blank" title="${s.url}">[${i+1}] ${s.title} (Rel: ${s.relevance})</a>`;
            });
        }
        
        resultsArea.innerHTML = html;

    } catch (err) {
        resultsArea.innerHTML = `<span style="color:red">Failed to connect to local backend. Is uvicorn running?</span>`;
    } finally {
        searchBtn.disabled = false;
        searchBtn.innerText = "Search";
    }
});
