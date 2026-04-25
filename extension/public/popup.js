document.getElementById('saveBtn').addEventListener('click', async () => {
    // Get the current active tab
    const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
    
    // Tell the content script on this tab to force a save
    chrome.tabs.sendMessage(tab.id, {type: 'FORCE_SAVE'});
    
    // Change button text to show it worked
    document.getElementById('saveBtn').innerText = "Sent!";
    setTimeout(() => {
        document.getElementById('saveBtn').innerText = "Force Save Current Page";
    }, 2000);
});
