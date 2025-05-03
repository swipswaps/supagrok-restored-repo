// Modules to control application life and create native browser window
const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path'); // Import the path module
// Use spawn for real-time output streaming, keep execFile for simpler scripts
const { execFile, spawn } = require('child_process');

console.log('[Main Process] Starting main process...'); // Log process start

function createWindow () {
  console.log('[Main Process] Creating browser window...');
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
  console.log('[Main Process] Loading index.html...');
  mainWindow.loadFile('index.html');

  // Open the DevTools.
  // mainWindow.webContents.openDevTools()
  console.log('[Main Process] Browser window created.');
}

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.whenReady().then(() => {
  console.log('[Main Process] Electron is ready.');
  createWindow();

  app.on('activate', function () {
    console.log('[Main Process] Activate event received.');
    // On macOS it's common to re-create a window in the app when the
    // dock icon is clicked and there are no other windows open.
    if (BrowserWindow.getAllWindows().length === 0) {
        console.log('[Main Process] No windows open, creating new one.');
        createWindow();
    }
  });
});

// --- IPC Handlers ---

// Listener for logs coming from the renderer process
ipcMain.on('log-to-main', (event, message) => {
  // Simply log the message received from the renderer, prefixed
  console.log(`[Renderer Process] ${message}`);
});

// Handle the 'run-script' request from the renderer using handle/invoke
ipcMain.handle('run-script', async (event, scriptPath, args = []) => {
  console.log(`[Main Process] Received 'run-script' request for script: [${scriptPath}], args: [${args.join(',')}]`);
  // Determine the absolute path to the script.
  const absoluteScriptPath = path.isAbsolute(scriptPath)
    ? scriptPath
    : path.join(__dirname, scriptPath);

  console.log(`[Main Process] Executing script (using execFile): ${absoluteScriptPath} with args: ${args.join(',')}`);

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
      if (stdout) console.log(`[Main Process] Script stdout (final buffer):\n${stdout}`);
      if (stderr) console.error(`[Main Process] Script stderr (final buffer):\n${stderr}`);
      console.log(`[Main Process] Script ${absoluteScriptPath} finished successfully (Code: 0)`);
      resolve({ error: null, stdout, stderr, code: 0 });
    });
  });
});

// Handle the 'upload-project' request from the renderer using spawn for real-time output
ipcMain.handle('upload-project', async (event, repoName) => {
  const scriptPath = path.join(__dirname, 'upload_to_github.sh');
  const scriptArgs = repoName ? [repoName] : [];

  console.log(`[Main Process] Received 'upload-project' request for repoName: [${repoName}], Type: [${typeof repoName}]`);

  // Validate repoName before spawning
  if (!repoName || typeof repoName !== 'string' || repoName.trim() === '') {
      const errorMsg = `[Main Process] Invalid or missing repoName received for upload-project. Aborting.`;
      console.error(errorMsg);
      return resolve({ // Resolve promise even on validation failure before spawn
          stdout: '',
          stderr: errorMsg,
          code: 1, // Indicate failure
          path: scriptPath
      });
  }

  console.log(`[Main Process] Spawning script: ${scriptPath} with args: ${scriptArgs.join(',') || '(none)'}`);

  return new Promise((resolve) => {
    const child = spawn(scriptPath, scriptArgs);
    console.log(`[Main Process] Spawned child process for ${scriptPath} (PID: ${child.pid})`);

    let fullStdout = '';
    let fullStderr = '';
    let spawnError = null;

    child.stdout.on('data', (data) => {
      const chunk = data.toString();
      process.stdout.write(chunk); // Real-time terminal output
      fullStdout += chunk;
    });

    child.stderr.on('data', (data) => {
      const chunk = data.toString();
      process.stderr.write(chunk); // Real-time terminal output
      fullStderr += chunk;
    });

    child.on('error', (error) => {
      console.error(`[Main Process] Spawn error for ${scriptPath} (PID: ${child.pid}): ${error}`);
      spawnError = error;
    });

    child.on('close', (code) => {
      console.log(`[Main Process] Script ${scriptPath} (PID: ${child.pid}) finished with exit code: ${code}`);
      if (spawnError) {
         resolve({
            stdout: fullStdout,
            stderr: `Spawn Error: ${spawnError.message}\n${fullStderr}`,
            code: spawnError.code || code || 1,
            path: scriptPath
        });
      } else {
         resolve({
            stdout: fullStdout,
            stderr: fullStderr,
            code: code,
            path: scriptPath
         });
      }
    });
  });
});

// --- App Lifecycle Events ---

app.on('window-all-closed', function () {
  console.log('[Main Process] All windows closed.');
  if (process.platform !== 'darwin') {
    console.log('[Main Process] Quitting application.');
    app.quit();
  } else {
    console.log('[Main Process] macOS detected, app remains active.');
  }
});

console.log('[Main Process] Main process script execution complete.'); // Log end of script
