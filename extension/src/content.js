let timeOnPage = 0;
let maxScrollDepth = 0;
let intervalId;

// Track time on page
intervalId = setInterval(() => {
    if (document.hasFocus()) {
        timeOnPage += 1;
    }
}, 1000);

// Track scroll depth
window.addEventListener('scroll', () => {
    const scrollHeight = document.documentElement.scrollHeight;
    const clientHeight = document.documentElement.clientHeight;
    const scrollTop = window.scrollY || document.documentElement.scrollTop;
    
    const maxScroll = scrollHeight - clientHeight;
    const currentScrollDepth = maxScroll > 0 ? (scrollTop / maxScroll) * 100 : 100;
    
    if (currentScrollDepth > maxScrollDepth) {
        maxScrollDepth = currentScrollDepth;
    }
});

// Calculate word count
function getWordCount(text) {
    return text.split(/\s+/).filter(word => word.length > 0).length;
}

// Clean text using a simple strategy for now (can add Readability.js later if imported via script tags)
function extractContent() {
    // simplified extraction
    const content = document.body.innerText;
    return {
        title: document.title,
        url: window.location.href,
        content: content,
        wordCount: getWordCount(content)
    };
}

// Ensure processing happens on page leave / unload
window.addEventListener('beforeunload', () => {
    clearInterval(intervalId);
    
    // Check constraints: Time > 30s AND Scroll > 40%, Word Count > 200
    const data = extractContent();
    if (timeOnPage >= 30 && maxScrollDepth >= 40 && data.wordCount >= 200) {
        // Send to background script
        chrome.runtime.sendMessage({
            type: 'INGEST_PAGE',
            payload: {
                ...data,
                timeSpent: timeOnPage,
                scrollDepth: maxScrollDepth,
                timestamp: new Date().toISOString()
            }
        });
    }
});

// Listen for explicit save requests from the popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'FORCE_SAVE') {
        const data = extractContent();
        chrome.runtime.sendMessage({
            type: 'INGEST_PAGE',
            payload: {
                ...data,
                timeSpent: timeOnPage,
                scrollDepth: maxScrollDepth,
                timestamp: new Date().toISOString()
            }
        });
        sendResponse({status: "forced_save_sent"});
    }
    return true;
});
