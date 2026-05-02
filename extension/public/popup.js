// Force Save functionality
document.getElementById('saveBtn').addEventListener('click', async () => {
    const btn = document.getElementById('saveBtn');
    try {
        const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
        chrome.tabs.sendMessage(tab.id, {type: 'FORCE_SAVE'});
        btn.innerText = "Ingesting into Brain...";
        btn.style.background = "#eef2ff";
        btn.style.color = "#4f46e5";
    } catch (e) {
        console.error(e);
        btn.innerText = "Failed (Reload tab)";
    }
    setTimeout(() => {
        btn.innerText = "Save Page to Brain";
        btn.style.background = "transparent";
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
    searchBtn.innerHTML = `Thinking<span class="thinking"></span>`;
    
    // Smooth transition reset
    resultsArea.classList.remove('active');
    
    setTimeout(async () => {
        resultsArea.innerHTML = "";
        resultsArea.classList.add('active');
        
        try {
            const response = await fetch('http://localhost:8000/api/v1/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query, top_k: 3 })
            });

            if (!response.ok) throw new Error("Server Error");

            const data = await response.json();
            
            if (data.error) {
                resultsArea.innerHTML = `<span style="color:#ef4444; font-weight:500;">Error: ${data.error}</span>`;
                return;
            }

            // Format Answer
            let answerStr = data.answer || "No answer returned.";
            // Simple markdown parsing for bold and paragraphs
            const formattedAnswer = answerStr
                .replace(/\n\n/g, '</p><p>')
                .replace(/\n/g, '<br>')
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

            let html = `<div class="answer-box"><p style="margin-top:0;">${formattedAnswer}</p></div>`;
            
            // Render Sources
            if (data.sources && data.sources.length > 0) {
                html += `<div style="font-size:0.75rem; color:#64748b; margin-bottom:6px; font-weight:600; text-transform:uppercase; letter-spacing:0.5px;">Citations</div>`;
                data.sources.forEach((s, i) => {
                    html += `<a class="source-link" href="${s.url}" target="_blank" title="${s.url}">[${i+1}] ${s.url}</a>`;
                });
            }
            
            resultsArea.innerHTML = html;

        } catch (err) {
            resultsArea.innerHTML = `<span style="color:#ef4444; font-weight:500;">Failed to connect to backend. Is Uvicorn running?</span>`;
        } finally {
            searchBtn.disabled = false;
            searchBtn.innerText = "Ask Agent";
        }
    }, 300); // Wait for collapse animation before fetching/showing
});

// Allow pressing Enter to search
document.getElementById('queryInput').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        document.getElementById('searchBtn').click();
    }
});
