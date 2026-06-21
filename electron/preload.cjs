const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("minebridge", {
  platform: process.platform,
  versions: process.versions,
  pickDirectory: (options = {}) =>
    ipcRenderer.invoke("minebridge:pick-directory", options),
  pickFile: (options = {}) => ipcRenderer.invoke("minebridge:pick-file", options)
});
