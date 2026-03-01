/**
 * AutoHound — Attack Path Intelligence Engine
 * Copyright (c) 2026 Gordon Prescott. All rights reserved.
 * 
 * ACH Research Division
 * Unauthorized copying, distribution, or modification of this software
 * without explicit written permission from Gordon Prescott is prohibited.
 */

const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 900,
    height: 700,
    frame: false,
    resizable: false,
    backgroundColor: '#0A0A0A',
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      enableRemoteModule: true
    },
    icon: path.join(__dirname, '../assets/autohound.ico')
  });

  mainWindow.loadFile('src/index.html');
  
  // Open DevTools in development
  // mainWindow.webContents.openDevTools();
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// IPC handlers for installation process
ipcMain.handle('check-system', async () => {
  // Check for Docker, Python, PowerShell
  return {
    docker: false, // Will implement actual checks
    python: false,
    powershell: true,
    apiKey: false,
    diskSpace: '14.2 GB'
  };
});

ipcMain.handle('start-install', async () => {
  // Execute installation commands
  return { success: true };
});
