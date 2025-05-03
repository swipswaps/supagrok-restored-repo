// Modules to control application life and create native browser window
const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path'); // Import the path module
const { execFile } = require('child_process');

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
ipcMain.handle('run-script', async (event, scriptPath, args = []) => {
  // Determine the absolute path to the script.
  // If scriptPath is already absolute, use it directly. Otherwise, join with __dirname.
  const absoluteScriptPath = path.isAbsolute(scriptPath)
    ? scriptPath
    : path.join(__dirname, scriptPath);

  console.log(`Executing script: ${absoluteScriptPath} with args: ${args.join(',')}`);

  // Use a Promise to wrap execFile for async/await with handle
  return new Promise((resolve) => {
    execFile(absoluteScriptPath, args, (error, stdout, stderr) => {
      if (error) {
        // Log the specific error, including ENOENT details if applicable
        console.error(`execFile error for run-script: ${error}`); // Full error object
        console.error(`Error Code: ${error.code}`); // Log specific code (e.g., ENOENT)
        console.error(`Attempted Path: ${absoluteScriptPath}`); // Log the path used
        // Resolve the promise with detailed error info for invoke
        resolve({
            error: `Script Execution Failed: ${error.message}`, // More descriptive error message
            code: error.code, // Include the error code (e.g., 'ENOENT')
            path: absoluteScriptPath, // Include the path that failed
            stdout: stdout || '',
            stderr: stderr || ''
        });
        return;
      }
      console.log(`Script stdout: ${stdout}`);
      console.error(`Script stderr: ${stderr}`); // Log stderr even on success
      // Resolve the promise with output for invoke
      resolve({ error: null, stdout, stderr, code: 0 });
    });
  });
});

// Handle the 'upload-project' request from the renderer (matching preload.js)
ipcMain.handle('upload-project', async (event, repoName) => { // Added repoName argument from preload
  // Use path.join with __dirname to ensure the path is correct
  const scriptPath = path.join(__dirname, 'upload_to_github.sh');
  console.log(`Executing script: ${scriptPath}`);

  return new Promise((resolve) => {
    // It's generally safer to provide the full path to the executable if known,
    // but execFile will search PATH if just the command name is given.
    // Ensure upload_to_github.sh has execute permissions (chmod +x).
    // Pass repoName as an argument if the script expects it.
    // If upload_to_github.sh doesn't need args, repoName will be undefined, and scriptArgs will be empty.
    const scriptArgs = repoName ? [repoName] : [];

    execFile(scriptPath, scriptArgs, (error, stdout, stderr) => {
      if (error) {
        console.error(`execFile error for upload-project: ${error}`); // Full error object
        console.error(`Error Code: ${error.code}`); // Log specific code
        console.error(`Attempted Path: ${scriptPath}`); // Log the path used
        // Return structured error information
        resolve({
            stdout: stdout || '',
            stderr: `Script Execution Failed: ${error.message}\n${stderr}`, // More descriptive
            code: error.code, // Include the error code
            path: scriptPath // Include the path that failed
        });
        return;
      }
      console.log(`Upload stdout: ${stdout}`);
      console.error(`Upload stderr: ${stderr}`); // Log stderr even on success
      resolve({ stdout, stderr, code: 0 }); // Indicate success with code 0
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
