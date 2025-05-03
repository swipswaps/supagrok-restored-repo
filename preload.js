// All of the Node.js APIs are available in the preload process.
// It has the same sandbox as a Chrome extension, but exposes APIs selectively.
const { contextBridge, ipcRenderer } = require('electron');

console.log('[Preload Script] Loading preload.js...'); // Log preload start

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld(
  'electronAPI', {
    // Expose a function to invoke 'run-script'
    runScript: (scriptPath, args) => {
        console.log(`[Preload Script] Invoking 'run-script' for: ${scriptPath}`);
        return ipcRenderer.invoke('run-script', scriptPath, args);
    },
    // Expose a function to invoke 'upload-project'
    uploadProject: (repoName) => {
        console.log(`[Preload Script] Invoking 'upload-project' for: ${repoName}`);
        return ipcRenderer.invoke('upload-project', repoName);
    },
    // Expose a function to send logs to the main process terminal
    logToMain: (message) => {
        // Using send for one-way logging is appropriate
        ipcRenderer.send('log-to-main', message);
    }
  }
);

console.log('[Preload Script] electronAPI exposed to main world.'); // Log preload end
