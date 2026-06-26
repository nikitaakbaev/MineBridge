"use strict";

const { spawn, spawnSync } = require("node:child_process");
const path = require("node:path");

/**
 * Locate a Python interpreter on the user's PATH.
 *
 * Returns an object with both a GUI-friendly command (used for the long-lived
 * backend so no console window appears) and a console command (used for
 * pip install — pythonw can choke on pip's progress bars / stderr buffering).
 * Returns null if no interpreter is reachable.
 */
function findPython() {
  const isWindows = process.platform === "win32";
  const candidates = isWindows ? ["pythonw", "python", "py"] : ["python3", "python"];

  for (const cmd of candidates) {
    const args = cmd === "py" ? ["-3", "--version"] : ["--version"];
    const result = spawnSync(cmd, args, { windowsHide: true });
    if (result.status !== 0) continue;

    const prefixArgs = cmd === "py" ? ["-3"] : [];
    let pipCommand = cmd;
    let pipPrefixArgs = prefixArgs;

    if (isWindows && cmd === "pythonw") {
      // pythonw works for the long-lived daemon, but pip install does better
      // through console python.exe — same directory, real stderr stream.
      const console = spawnSync("python", ["--version"], { windowsHide: true });
      if (console.status === 0) {
        pipCommand = "python";
        pipPrefixArgs = [];
      }
    }

    const version = (result.stdout?.toString() || result.stderr?.toString() || "").trim();

    return { command: cmd, prefixArgs, pipCommand, pipPrefixArgs, version };
  }
  return null;
}

/**
 * Check whether the backend Python package is already importable.
 */
function isBackendInstalled(python) {
  if (!python) return false;
  const result = spawnSync(
    python.command,
    [...python.prefixArgs, "-c", "import minebridge_frp.app.api.main"],
    { windowsHide: true }
  );
  return result.status === 0;
}

/**
 * Run ``pip install`` to install the backend on first launch. Buffers full
 * output and includes it in the rejection error so the caller can show it
 * to the user.
 */
function installBackend(python, backendDir, onLog) {
  return new Promise((resolve, reject) => {
    const args = [
      ...python.pipPrefixArgs,
      "-m",
      "pip",
      "install",
      "--user",
      "--upgrade",
      "--disable-pip-version-check",
      "--no-warn-script-location",
      backendDir
    ];
    const child = spawn(python.pipCommand, args, {
      windowsHide: true,
      stdio: ["ignore", "pipe", "pipe"]
    });

    const buffer = [];
    const collect = (chunk) => {
      const text = chunk.toString();
      buffer.push(text);
      onLog?.(text);
    };
    child.stdout.on("data", collect);
    child.stderr.on("data", collect);

    child.on("error", (err) => {
      const error = new Error(`Не удалось запустить pip: ${err.message}`);
      error.log = buffer.join("");
      reject(error);
    });
    child.on("exit", (code) => {
      if (code === 0) return resolve();
      const error = new Error(`pip install завершился с кодом ${code}`);
      error.log = buffer.join("");
      reject(error);
    });
  });
}

/**
 * Start the FastAPI backend in a hidden subprocess. Returns the spawned
 * ChildProcess so the main process can kill it on quit.
 */
function spawnBackend(python, cwd, onStdout, onStderr, onExit) {
  const args = [...python.prefixArgs, "-m", "minebridge_frp.app.api.main"];
  const child = spawn(python.command, args, {
    cwd,
    env: { ...process.env, PYTHONUNBUFFERED: "1" },
    stdio: ["ignore", "pipe", "pipe"],
    windowsHide: true
  });
  child.stdout.on("data", (chunk) => onStdout?.(chunk.toString().trim()));
  child.stderr.on("data", (chunk) => onStderr?.(chunk.toString().trim()));
  child.on("exit", (code) => onExit?.(code));
  return child;
}

module.exports = {
  findPython,
  isBackendInstalled,
  installBackend,
  spawnBackend
};
