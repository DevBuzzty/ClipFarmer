const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

let mainWindow;
let pythonProcess;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1280,
        height: 850,
        title: "Twitch Viral Clip Automator v2.0",
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            nodeIntegration: false,
            contextIsolation: true,
        },
        backgroundColor: '#0b001a',
        show: false
    });

    mainWindow.loadFile(path.join(__dirname, 'index.html'));
    mainWindow.once('ready-to-show', () => mainWindow.show());
}

function startBackend() {
    const isDev = !app.isPackaged;
    const port = "5001";
    let backendPath;
    let args = [];

    if (isDev) {
        backendPath = path.join(__dirname, '../backend/app.py');
        args = [backendPath];
        pythonProcess = spawn('python', args, { env: { ...process.env, PORT: port } });
    } else {
        const possiblePaths = [
            path.join(process.resourcesPath, 'backend', 'app.exe'),
            path.join(path.dirname(app.getPath('exe')), 'resources', 'backend', 'app.exe')
        ];
        backendPath = possiblePaths.find(p => fs.existsSync(p));
        if (backendPath) {
            pythonProcess = spawn(backendPath, [], { windowsHide: true, env: { ...process.env, PORT: port } });
        } else {
            dialog.showErrorBox("Backend Error", "Konnte app.exe nicht finden.");
        }
    }

    if (pythonProcess) {
        pythonProcess.on('error', (err) => {
            dialog.showErrorBox("Backend Startfehler", err.message);
        });
        pythonProcess.on('exit', (code) => {
            if (code !== 0 && code !== null) {
                dialog.showErrorBox("Backend Exit", `Backend beendet mit Code ${code}`);
            }
        });
    }
}

app.whenReady().then(() => {
    startBackend();
    createWindow();
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit();
    if (pythonProcess) pythonProcess.kill();
});

ipcMain.on('restart-backend', () => {
    if (pythonProcess) pythonProcess.kill();
    startBackend();
});
