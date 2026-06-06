#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${MINEBRIDGE_BUILD_VENV:-"$ROOT_DIR/.venv-build"}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "$ROOT_DIR"

"$PYTHON_BIN" -m venv "$VENV_DIR"
"$VENV_DIR/bin/python" -m pip install --upgrade pip
"$VENV_DIR/bin/python" -m pip install -e ".[packaging]"
"$VENV_DIR/bin/python" -m PyInstaller --noconfirm --clean packaging/minebridge-frp.spec

printf '\nLinux portable build is ready: %s\n' "$ROOT_DIR/dist/MineBridge FRP"
