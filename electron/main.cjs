"use strict";

const { app, BrowserWindow, Menu, dialog, ipcMain } = require("electron");
const path = require("node:path");
const fs = require("node:fs");
const crypto = require("node:crypto");

const {
  findPython,
  isBackendInstalled,
  installBackend,
  spawnBackend,
  spawnBundledBackend,
  bundledBackendExecutable
} = require("./backend.cjs");

const isDev = !app.isPackaged;
let backendProcess = null;
let mainWindow = null;
let splashWindow = null;
const apiToken = crypto.randomBytes(32).toString("hex");
process.env.MINEBRIDGE_API_TOKEN = apiToken;

function bundledBackendDir() {
  // In packaged builds extraResources puts pyproject.toml + minebridge_frp under
  // process.resourcesPath/backend. In dev we install the editable package
  // directly from the working tree.
  return isDev
    ? path.resolve(__dirname, "..")
    : path.join(process.resourcesPath, "backend");
}

function backendCwd() {
  return isDev ? path.resolve(__dirname, "..") : bundledBackendDir();
}

function showSplash(message) {
  if (splashWindow) {
    splashWindow.webContents.executeJavaScript(
      `document.getElementById("splash-message").textContent = ${JSON.stringify(message)};`
    );
    return;
  }
  splashWindow = new BrowserWindow({
    width: 480,
    height: 220,
    frame: false,
    resizable: false,
    backgroundColor: "#08111f",
    show: true,
    skipTaskbar: false,
    webPreferences: { contextIsolation: true, nodeIntegration: false }
  });
  const html = `
    <html><head><meta charset="utf-8"><style>
      body{margin:0;background:#08111f;color:#cbd5f5;font:14px/1.4 "Segoe UI",system-ui,sans-serif;
           display:flex;flex-direction:column;justify-content:center;align-items:center;height:100vh;}
      h1{margin:0 0 12px;font-size:18px;color:#f1f5f9;}
      .dot{width:10px;height:10px;border-radius:50%;background:#7dd3fc;margin-bottom:14px;
           box-shadow:0 0 0 6px rgba(125,211,252,0.18);animation:p 1.6s ease-in-out infinite;}
      @keyframes p{0%,100%{opacity:.3}50%{opacity:1}}
      p{margin:0;color:#94a3b8;font-size:13px;}
    </style></head><body>
      <div class="dot"></div>
      <h1>MineBridge FRP</h1>
      <p id="splash-message">${message}</p>
    </body></html>`;
  splashWindow.loadURL("data:text/html;charset=utf-8," + encodeURIComponent(html));
}

function closeSplash() {
  if (splashWindow) {
    splashWindow.close();
    splashWindow = null;
  }
}

async function ensureBackendReady() {
  if (!isDev && bundledBackendExecutable(process.resourcesPath)) {
    return { bundled: true };
  }

  const python = findPython();
  if (!python) {
    dialog.showErrorBox(
      "Python не найден",
      "MineBridge требует Python 3.11+ в PATH.\n\n" +
        "1) Скачайте с https://www.python.org/downloads/ (версия 3.11 или 3.12, не 3.13+).\n" +
        '2) При установке отметьте "Add python.exe to PATH".\n' +
        "3) Запустите MineBridge снова."
    );
    app.quit();
    return null;
  }

  if (!isBackendInstalled(python)) {
    showSplash("Устанавливаем backend (это занимает 30-60 секунд)…");
    const dir = bundledBackendDir();
    if (!fs.existsSync(path.join(dir, "pyproject.toml"))) {
      dialog.showErrorBox(
        "Backend не найден",
        `Не удалось найти pyproject.toml в ${dir}. Переустановите MineBridge.`
      );
      app.quit();
      return null;
    }
    try {
      await installBackend(python, dir, (line) => {
        if (splashWindow) {
          const last = String(line).trim().split(/\r?\n/).slice(-1)[0] || "…";
          splashWindow.webContents
            .executeJavaScript(
              `document.getElementById("splash-message").textContent = ${JSON.stringify(last)};`
            )
            .catch(() => {});
        }
      });
    } catch (err) {
      const logTail = (err.log || String(err.message || err))
        .split(/\r?\n/)
        .filter(Boolean)
        .slice(-25)
        .join("\n");
      const logPath = path.join(app.getPath("userData"), "pip-install-error.log");
      try {
        fs.writeFileSync(logPath, err.log || String(err.message || err), "utf8");
      } catch {
        /* best-effort */
      }
      dialog.showErrorBox(
        "Не удалось установить backend",
        `Python: ${python.version || python.command}\n` +
          `Полный лог: ${logPath}\n\n` +
          `Последние строки:\n${logTail}`
      );
      app.quit();
      return null;
    }
  }
  return python;
}

function startBackend(python) {
  const onStdout = (line) => console.log(`[backend] ${line}`);
  const onStderr = (line) => console.error(`[backend] ${line}`);
  const onExit = (code) => {
    console.log(`[backend] exited with code ${code}`);
    backendProcess = null;
  };
  const env = { MINEBRIDGE_API_TOKEN: apiToken };
  const bundledExecutable = !isDev ? bundledBackendExecutable(process.resourcesPath) : null;
  backendProcess = bundledExecutable
    ? spawnBundledBackend(bundledExecutable, env, onStdout, onStderr, onExit)
    : spawnBackend(python, backendCwd(), onStdout, onStderr, onExit, env);
  backendProcess.on("error", (err) => {
    console.error(`[backend] failed to spawn: ${err.message}`);
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
    show: false,
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  mainWindow.once("ready-to-show", () => {
    closeSplash();
    mainWindow.show();
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

  app.whenReady().then(async () => {
    if (!isDev) showSplash("Подготавливаем приложение…");
    const python = await ensureBackendReady();
    if (!python) return;
    startBackend(python);
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
