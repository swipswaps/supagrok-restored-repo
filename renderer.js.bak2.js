// This file is required by the index.html file and will
// be executed in the renderer process for that window.

// Log renderer process start
window.electronAPI.logToMain('Renderer process script started.');

// Function to run general scripts
async function runScript(scriptPath, args = []) {
    window.electronAPI.logToMain(`runScript called for: ${scriptPath}, Args: ${JSON.stringify(args)}`);
    const outputElement = document.getElementById('output');
    outputElement.textContent = `Executing ${scriptPath}...\n`; // Clear previous output
    try {
        window.electronAPI.logToMain(`Sending 'run-script' IPC message for ${scriptPath}...`);
        const result = await window.electronAPI.runScript(scriptPath, args);
        window.electronAPI.logToMain(`Received response for 'run-script' IPC message for ${scriptPath}. Code: ${result.code}`);
        outputElement.textContent += `\n--- Script Output ---\n`;
        if (result.stdout) {
            outputElement.textContent += `Stdout:\n${result.stdout}\n`;
        }
        if (result.stderr) {
            outputElement.textContent += `Stderr:\n${result.stderr}\n`;
        }
        if (result.error) {
             outputElement.textContent += `Error: ${result.error}\nCode: ${result.code}\nPath: ${result.path}\n`;
             window.electronAPI.logToMain(`'run-script' for ${scriptPath} resulted in error: ${result.error}`);
        } else {
             outputElement.textContent += `\n--- Completed Successfully (Code: ${result.code}) ---\n`;
             window.electronAPI.logToMain(`'run-script' for ${scriptPath} completed successfully.`);
        }
    } catch (error) {
        outputElement.textContent += `\n--- IPC Error ---\nError: ${error.message}\n`;
        window.electronAPI.logToMain(`IPC Error during 'run-script' for ${scriptPath}: ${error.message}`);
        console.error('IPC Error:', error); // Also log to renderer console
    }
}

// Function to handle GitHub upload, now with prompt and logging
async function uploadProject() {
    window.electronAPI.logToMain('uploadProject function called (button clicked).');
    const outputElement = document.getElementById('output');
    outputElement.textContent = 'Preparing GitHub upload...\n'; // Clear previous output

    window.electronAPI.logToMain('Displaying prompt for repository name...');
    const repoName = prompt("Enter target GitHub repository (e.g., owner/repo):");

    if (repoName === null || repoName.trim() === "") {
        outputElement.textContent += 'GitHub upload cancelled by user.\n';
        window.electronAPI.logToMain('User cancelled or entered empty repository name.');
        return; // Abort if user cancels or enters nothing
    }
    window.electronAPI.logToMain(`User entered repository name: ${repoName}`);

    outputElement.textContent += `Attempting GitHub upload for ${repoName} via gh...\n`;
    try {
        window.electronAPI.logToMain(`Sending 'upload-project' IPC message for ${repoName}...`);
        const result = await window.electronAPI.uploadProject(repoName);
        window.electronAPI.logToMain(`Received response for 'upload-project' IPC message for ${repoName}. Code: ${result.code}`);
        outputElement.textContent += `\n--- Upload Result ---\n`;
        if (result.stdout) {
            outputElement.textContent += `Stdout:\n${result.stdout}\n`;
        }
        if (result.stderr) {
            outputElement.textContent += `Stderr:\n${result.stderr}\n`;
        }
        if (result.code !== 0) {
             outputElement.textContent += `\n--- Failed (Code: ${result.code}) ---\n`;
             window.electronAPI.logToMain(`'upload-project' for ${repoName} failed. Code: ${result.code}`);
        } else {
             outputElement.textContent += `\n--- Completed Successfully (Code: ${result.code}) ---\n`;
             window.electronAPI.logToMain(`'upload-project' for ${repoName} completed successfully.`);
        }
    } catch (error) {
        outputElement.textContent += `\n--- IPC Error ---\nError: ${error.message}\n`;
        window.electronAPI.logToMain(`IPC Error during 'upload-project' for ${repoName}: ${error.message}`);
        console.error('IPC Error:', error); // Also log to renderer console
    }
}

window.electronAPI.logToMain('Renderer process script finished loading.');
