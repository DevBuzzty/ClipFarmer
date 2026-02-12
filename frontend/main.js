const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const dotenv = require('dotenv');
const fs = require('fs');

dotenv.config();

let mainWindow;
let pythonProcess;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
    backgroundColor: '#0b0d17', // Dark space background
  });

  mainWindow.loadFile(path.join(__dirname, 'index.html'));

  // Open DevTools in development
  // mainWindow.webContents.openDevTools();
}

function startPythonBackend() {
  const isDev = !app.isPackaged;
  let backendPath;
  let args = [];

  if (isDev) {
    const pythonPath = process.env.PYTHON_PATH || 'python';
    backendPath = path.join(__dirname, '../backend/app.py');
    args = [backendPath];

    if (!fs.existsSync(backendPath)) {
      console.error(`Backend script not found at ${backendPath}`);
      return;
    }

    pythonProcess = spawn(pythonPath, args);
  } else {
    // Try multiple possible locations for production
    const possiblePaths = [
      path.join(process.resourcesPath, 'backend', 'app.exe'),
      path.join(process.resourcesPath, 'app.asar.unpacked', 'backend', 'app.exe'),
      path.join(path.dirname(app.getPath('exe')), 'resources', 'backend', 'app.exe')
    ];

    backendPath = possiblePaths.find(p => fs.existsSync(p));

    if (!backendPath) {
      const errorMsg = `Backend executable not found. Searched in:\n${possiblePaths.join('\n')}`;
      console.error(errorMsg);
      dialog.showErrorBox('Backend Fehler', errorMsg);
      return;
    }

    try {
      pythonProcess = spawn(backendPath, [], {
        windowsHide: true,
        shell: false
      });
    } catch (err) {
      console.error('Failed to spawn backend process:', err);
      dialog.showErrorBox('Backend Fehler', `Konnte Backend nicht starten: ${err.message}`);
      return;
    }
  }

  if (pythonProcess) {
    const logPath = path.join(app.getPath('userData'), 'backend.log');
    const logStream = fs.createWriteStream(logPath, { flags: 'a' });

    pythonProcess.on('error', (err) => {
      console.error('Failed to start backend process:', err);
      logStream.write(`ERROR: Failed to start backend process: ${err.message}\n`);
      dialog.showErrorBox('Backend Fehler', `Konnte Backend-Prozess nicht starten: ${err.message}\nLogs: ${logPath}`);
    });

    pythonProcess.on('exit', (code, signal) => {
      console.log(`Backend process exited with code ${code} and signal ${signal}`);
      logStream.write(`EXIT: Backend process exited with code ${code} and signal ${signal}\n`);
      if (code !== 0 && code !== null) {
        dialog.showErrorBox('Backend Fehler', `Backend-Prozess wurde unerwartet beendet (Code: ${code}).\nLogs: ${logPath}`);
      }
    });

    pythonProcess.stdout.on('data', (data) => {
      console.log(`Python: ${data}`);
      logStream.write(`STDOUT: ${data}\n`);
    });

    pythonProcess.stderr.on('data', (data) => {
      console.error(`Python Error: ${data}`);
      logStream.write(`STDERR: ${data}\n`);
    });
  }
}

app.whenReady().then(() => {
  startPythonBackend();
  createWindow();

  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit();
  if (pythonProcess) pythonProcess.kill();
});
