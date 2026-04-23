chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'INGEST_PAGE') {
        const payload = message.payload;
        
        // Exclude specific domains/protocols
        if (payload.url.startsWith('chrome://') || payload.url.includes('google.com/search')) {
            return;
        }

        console.log("Sending document for ingestion:", payload.title);

        fetch('http://localhost:8000/api/v1/ingest', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        })
        .then(response => response.json())
        .then(data => {
            console.log('Ingestion Response:', data);
        })
        .catch(error => {
            console.error('Ingestion Error:', error);
        });
    }
    return true;
});
