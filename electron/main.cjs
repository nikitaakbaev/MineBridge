const { app, BrowserWindow, Menu, dialog, ipcMain } = require("electron");
const { spawn } = require("node:child_process");
const path = require("node:path");

const isDev = !app.isPackaged;
let backendProcess = null;
let mainWindow = null;

function startBackend() {
  const customCommand = process.env.MINEBRIDGE_BACKEND_CMD;
  const command = customCommand || process.env.PYTHON || "python3";
  const args = customCommand ? [] : ["-m", "minebridge_frp.app.api.main"];

  backendProcess = spawn(command, args, {
    cwd: path.resolve(__dirname, ".."),
    env: {
      ...process.env,
      PYTHONUNBUFFERED: "1"
    },
    shell: Boolean(customCommand),
    stdio: ["ignore", "pipe", "pipe"]
  });

  backendProcess.stdout.on("data", (chunk) => {
    console.log(`[backend] ${chunk.toString().trim()}`);
  });
  backendProcess.stderr.on("data", (chunk) => {
    console.error(`[backend] ${chunk.toString().trim()}`);
  });
  backendProcess.on("exit", (code) => {
    console.log(`[backend] exited with code ${code}`);
    backendProcess = null;
  });
}

function createWindow() {
  Menu.setApplicationMenu(null);

  mainWindow = new BrowserWindow({
    width: 1320,
    height: 860,
    minWidth: 1040,
    minHeight: 680,
    title: "MineBridge",
    backgroundColor: "#08111f",
    titleBarStyle: "hiddenInset",
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  if (isDev) {
    mainWindow.loadURL("http://127.0.0.1:5173");
  } else {
    mainWindow.loadFile(path.join(__dirname, "../dist-electron/renderer/index.html"));
  }
}

ipcMain.handle("minebridge:pick-directory", async (_event, options = {}) => {
  const target = mainWindow ?? BrowserWindow.getFocusedWindow();
  const result = await dialog.showOpenDialog(target, {
    title: options.title || "Выберите папку",
    defaultPath: options.defaultPath || undefined,
    properties: ["openDirectory", "createDirectory"]
  });
  if (result.canceled || result.filePaths.length === 0) return null;
  return result.filePaths[0];
});

ipcMain.handle("minebridge:pick-file", async (_event, options = {}) => {
  const target = mainWindow ?? BrowserWindow.getFocusedWindow();
  const filters = Array.isArray(options.filters) && options.filters.length > 0
    ? options.filters
    : [{ name: "Все файлы", extensions: ["*"] }];
  const result = await dialog.showOpenDialog(target, {
    title: options.title || "Выберите файл",
    defaultPath: options.defaultPath || undefined,
    filters,
    properties: ["openFile"]
  });
  if (result.canceled || result.filePaths.length === 0) return null;
  return result.filePaths[0];
});

const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
  app.quit();
} else {
  app.on("second-instance", () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });

  app.whenReady().then(() => {
    startBackend();
    createWindow();
  });

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });

  app.on("window-all-closed", () => {
    if (process.platform !== "darwin") app.quit();
  });

  app.on("before-quit", () => {
    if (backendProcess) backendProcess.kill();
  });
}
