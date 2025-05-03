// Modules to control application life and create native browser window
const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path'); // Import the path module
// Use spawn for real-time output streaming, keep execFile for simpler scripts
const { execFile, spawn } = require('child_process');

function createWindow () {
  // Create the browser window.
  const mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true, // Recommended for security
      nodeIntegration: false // Recommended for security
    }
  });

  // and load the index.html of the app.
  mainWindow.loadFile('index.html');

  // Open the DevTools.
  // mainWindow.webContents.openDevTools()
}

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.whenReady().then(() => {
  createWindow();

  app.on('activate', function () {
    // On macOS it's common to re-create a window in the app when the
    // dock icon is clicked and there are no other windows open.
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

// Handle the 'run-script' request from the renderer using handle/invoke
// Keep using execFile here as real-time output might not be needed for all scripts
ipcMain.handle('run-script', async (event, scriptPath, args = []) => {
  // Determine the absolute path to the script.
  // If scriptPath is already absolute, use it directly. Otherwise, join with __dirname.
  const absoluteScriptPath = path.isAbsolute(scriptPath)
    ? scriptPath
    : path.join(__dirname, scriptPath);

  console.log(`[Main Process] Executing script (using execFile): ${absoluteScriptPath} with args: ${args.join(',')}`);

  // Use a Promise to wrap execFile for async/await with handle
  return new Promise((resolve) => {
    execFile(absoluteScriptPath, args, (error, stdout, stderr) => {
      if (error) {
        console.error(`[Main Process] execFile error for run-script: ${error}`);
        console.error(`[Main Process] Error Code: ${error.code}`);
        console.error(`[Main Process] Attempted Path: ${absoluteScriptPath}`);
        resolve({
            error: `Script Execution Failed: ${error.message}`,
            code: error.code,
            path: absoluteScriptPath,
            stdout: stdout || '',
            stderr: stderr || ''
        });
        return;
      }
      // Log final output to console as well for consistency
      if (stdout) console.log(`[Main Process] Script stdout:\n${stdout}`);
      if (stderr) console.error(`[Main Process] Script stderr:\n${stderr}`);
      console.log(`[Main Process] Script finished successfully (Code: 0)`);
      resolve({ error: null, stdout, stderr, code: 0 });
    });
  });
});

// Handle the 'upload-project' request from the renderer using spawn for real-time output
ipcMain.handle('upload-project', async (event, repoName) => {
  const scriptPath = path.join(__dirname, 'upload_to_github.sh');
  const scriptArgs = repoName ? [repoName] : [];

  console.log(`[Main Process] Received 'upload-project' for repoName: [${repoName}], Type: [${typeof repoName}]`);
  console.log(`[Main Process] Spawning script: ${scriptPath} with args: ${scriptArgs.join(',') || '(none)'}`);

  return new Promise((resolve) => {
    const child = spawn(scriptPath, scriptArgs);

    let fullStdout = '';
    let fullStderr = '';
    let spawnError = null; // To capture potential errors during spawn itself

    // Listen for stdout data
    child.stdout.on('data', (data) => {
      const chunk = data.toString();
      process.stdout.write(chunk); // Write directly to main process stdout (real-time terminal)
      fullStdout += chunk; // Accumulate for final result
    });

    // Listen for stderr data
    child.stderr.on('data', (data) => {
      const chunk = data.toString();
      process.stderr.write(chunk); // Write directly to main process stderr (real-time terminal)
      fullStderr += chunk; // Accumulate for final result
    });

    // Listen for errors during spawn/execution (e.g., command not found)
    child.on('error', (error) => {
      console.error(`[Main Process] Spawn error for ${scriptPath}: ${error}`);
      spawnError = error; // Store the error
      // Don't resolve here, wait for 'close' event
    });

    // Listen for the script process to close
    child.on('close', (code) => {
      console.log(`[Main Process] Script ${scriptPath} finished with exit code: ${code}`);
      // Resolve the promise with collected data and exit code
      if (spawnError) {
        // If a spawn error occurred, prioritize reporting that
         resolve({
            stdout: fullStdout,
            stderr: `Spawn Error: ${spawnError.message}\n${fullStderr}`,
            code: spawnError.code || code || 1, // Use spawn error code or exit code or default to 1
            path: scriptPath
        });
      } else {
         resolve({
            stdout: fullStdout,
            stderr: fullStderr,
            code: code, // The actual exit code from the script
            path: scriptPath
         });
      }
    });
  });
});

// Quit when all windows are closed, except on macOS. There, it's common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit();
});

// In this file you can include the rest of your app's specific main process
// code. You can also put them in separate files and require them here.
