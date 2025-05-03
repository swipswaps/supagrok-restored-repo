// This file is required by the index.html file and will
// be executed in the renderer process for that window.
// No Node.js APIs are available in this process because
// `nodeIntegration` is turned off and `contextIsolation` is turned on.
// Use the contextBridge API in `preload.js` to expose Node.js functionality
// to the renderer process.

// Function to run general scripts
async function runScript(scriptPath, args = []) {
    const outputElement = document.getElementById('output');
    outputElement.textContent = `Executing ${scriptPath}...\n`; // Clear previous output
    try {
        // Use the exposed electronAPI from preload.js
        const result = await window.electronAPI.runScript(scriptPath, args);
        outputElement.textContent += `\n--- Script Output ---\n`;
        if (result.stdout) {
            outputElement.textContent += `Stdout:\n${result.stdout}\n`;
        }
        if (result.stderr) {
            outputElement.textContent += `Stderr:\n${result.stderr}\n`;
        }
        if (result.error) {
             outputElement.textContent += `Error: ${result.error}\nCode: ${result.code}\nPath: ${result.path}\n`;
        } else {
             outputElement.textContent += `\n--- Completed Successfully (Code: ${result.code}) ---\n`;
        }
    } catch (error) {
        outputElement.textContent += `\n--- IPC Error ---\nError: ${error.message}\n`;
        console.error('IPC Error:', error);
    }
}

// Function to handle GitHub upload, now with prompt
async function uploadProject() {
    const outputElement = document.getElementById('output');
    outputElement.textContent = 'Preparing GitHub upload...\n'; // Clear previous output

    const repoName = prompt("Enter target GitHub repository (e.g., owner/repo):");

    if (repoName === null || repoName.trim() === "") {
        outputElement.textContent += 'GitHub upload cancelled by user.\n';
        console.log('GitHub upload cancelled.');
        return; // Abort if user cancels or enters nothing
    }

    outputElement.textContent += `Attempting GitHub upload for ${repoName} via gh...\n`;
    try {
        // Use the exposed electronAPI from preload.js, passing the repoName
        const result = await window.electronAPI.uploadProject(repoName);
        outputElement.textContent += `\n--- Upload Result ---\n`;
        if (result.stdout) {
            outputElement.textContent += `Stdout:\n${result.stdout}\n`;
        }
        if (result.stderr) {
            outputElement.textContent += `Stderr:\n${result.stderr}\n`;
        }
        if (result.code !== 0) {
             outputElement.textContent += `\n--- Failed (Code: ${result.code}) ---\n`;
        } else {
             outputElement.textContent += `\n--- Completed Successfully (Code: ${result.code}) ---\n`;
        }
    } catch (error) {
        outputElement.textContent += `\n--- IPC Error ---\nError: ${error.message}\n`;
        console.error('IPC Error:', error);
    }
}

// Make functions available globally or attach to buttons in index.html
// Since index.html uses onclick="electronAPI.runScript(...)" etc.,
// we need to make sure those functions exist on the electronAPI object
// exposed via preload. Let's adjust index.html and preload slightly.

// No need to expose runScript and uploadProject globally here if
// index.html calls window.electronAPI directly.
