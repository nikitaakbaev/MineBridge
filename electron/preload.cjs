const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("minebridge", {
  platform: process.platform,
  versions: process.versions,
  apiToken: process.env.MINEBRIDGE_API_TOKEN || "",
  pickDirectory: (options = {}) =>
    ipcRenderer.invoke("minebridge:pick-directory", options),
  pickFile: (options = {}) => ipcRenderer.invoke("minebridge:pick-file", options)
});
