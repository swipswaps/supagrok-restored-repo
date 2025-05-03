// /home/owner/Documents/scripts/AICode/680fddc4-f7f8-8008-a24f-ccde790499ca/app/supagrok_restored_repo/preload.js
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // Keep existing function if needed
  runScript: (scriptPath, args) => ipcRenderer.invoke('run-script', scriptPath, args),
  // Add the new function for uploading
  uploadProject: (repoName) => ipcRenderer.invoke('upload-project', repoName),
  // Optional: Listener for streaming output if you implement that in main.js
  // onScriptOutput: (callback) => ipcRenderer.on('script-output', (_event, value) => callback(value))
});
