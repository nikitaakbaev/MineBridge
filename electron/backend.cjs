"use strict";

const { spawn, spawnSync } = require("node:child_process");
const path = require("node:path");

/**
 * Locate a Python interpreter on the user's PATH.
 *
 * Returns the python command string ("python3", "python", "py -3") or null if
 * none is reachable. We try the GUI-friendly variants (pythonw / py -3) first
 * for Windows so that no console window flashes when we eventually spawn the
 * backend.
 */
function findPython() {
  const candidates =
    process.platform === "win32"
      ? ["pythonw", "python", "py"]
      : ["python3", "python"];

  for (const cmd of candidates) {
    const args = cmd === "py" ? ["-3", "--version"] : ["--version"];
    const result = spawnSync(cmd, args, { windowsHide: true });
    if (result.status === 0) return { command: cmd, prefixArgs: cmd === "py" ? ["-3"] : [] };
  }
  return null;
}

/**
 * Check whether ``minebridge-frp-api`` (and therefore the Python package) is
 * already installed by importing the backend module.
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
 * Run ``pip install -e <bundled-backend-dir>`` to install the backend on first
 * launch. Output is forwarded to ``onLog`` for the splash screen.
 */
function installBackend(python, backendDir, onLog) {
  return new Promise((resolve, reject) => {
    const args = [
      ...python.prefixArgs,
      "-m",
      "pip",
      "install",
      "--user",
      "--upgrade",
      backendDir
    ];
    const child = spawn(python.command, args, {
      windowsHide: true,
      stdio: ["ignore", "pipe", "pipe"]
    });
    child.stdout.on("data", (chunk) => onLog?.(chunk.toString()));
    child.stderr.on("data", (chunk) => onLog?.(chunk.toString()));
    child.on("error", reject);
    child.on("exit", (code) => {
      if (code === 0) resolve();
      else reject(new Error(`pip install exited with code ${code}`));
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
