#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)

APP_BIN="$PROJECT_ROOT/.venv/bin/minebridge-frp"
PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"

cd "$PROJECT_ROOT"

if [[ -x "$APP_BIN" ]]; then
  exec "$APP_BIN" "$@"
fi

if [[ -x "$PYTHON_BIN" ]]; then
  exec "$PYTHON_BIN" -m minebridge_frp.app.electron_launcher "$@"
fi

if command -v minebridge-frp >/dev/null 2>&1; then
  exec minebridge-frp "$@"
fi

printf 'MineBridge FRP launcher error: .venv is not ready in %s\n' "$PROJECT_ROOT" >&2
printf 'Create it with: python -m venv .venv && .venv/bin/pip install -e ".[dev]"\n' >&2
exit 1
