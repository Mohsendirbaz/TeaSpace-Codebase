const path = require('path');
const { app, BrowserWindow, Menu, dialog } = require('electron');
const isDev = require('electron-is-dev');
const fs = require('fs').promises;

function createWindow() {
 const win = new BrowserWindow({
   width: 800,
   height: 600,
   webPreferences: {
     nodeIntegration: true,
     contextIsolation: false
   }
 });

 const template = [
   {
     label: 'File',
     submenu: [
       {
         label: 'Save',
         accelerator: 'CmdOrCtrl+S',
         click: async () => {
           const data = await win.webContents.executeJavaScript(
             `window.getAppData && window.getAppData()`
           );

           const { filePath } = await dialog.showSaveDialog({
             buttonLabel: 'Save',
             defaultPath: 'dashboard-data.json'
           });

           if (filePath) {
             await fs.writeFile(filePath, JSON.stringify(data));
           }
         }
       },
       { type: 'separator' },
       { role: 'quit' }
     ]
   },
   {
     label: 'Edit',
     submenu: [
       { role: 'undo' },
       { role: 'redo' },
       { type: 'separator' },
       { role: 'cut' },
       { role: 'copy' },
       { role: 'paste' }
     ]
   },
   {
     label: 'View',
     submenu: [
       { role: 'reload' },
       { role: 'toggleDevTools' },
       { type: 'separator' },
       { role: 'resetZoom' },
       { role: 'zoomIn' },
       { role: 'zoomOut' }
     ]
   }
 ];

 const menu = Menu.buildFromTemplate(template);
 Menu.setApplicationMenu(menu);

 win.loadURL(
   isDev
     ? 'http://localhost:3000'
     : `file://${path.join(__dirname, '../build/index.html')}`
 );
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