#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)

APP_BIN="$PROJECT_ROOT/.venv/bin/minebridge-frp"
QT_APP_BIN="$PROJECT_ROOT/.venv/bin/minebridge-frp-qt"
PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"

cd "$PROJECT_ROOT"

if [[ "${MINEBRIDGE_USE_QT:-}" == "1" ]]; then
  if [[ -x "$QT_APP_BIN" ]]; then
    exec "$QT_APP_BIN" "$@"
  fi
  if [[ -x "$PYTHON_BIN" ]]; then
    exec "$PYTHON_BIN" -m minebridge_frp.app.main "$@"
  fi
fi

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
