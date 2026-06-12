const { contextBridge } = require("electron");

contextBridge.exposeInMainWorld("minebridge", {
  platform: process.platform,
  versions: process.versions
});
