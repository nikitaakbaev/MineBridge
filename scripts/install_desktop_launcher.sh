#!/usr/bin/env bash
set -euo pipefail

APP_ID="minebridge-frp"
APP_NAME="MineBridge FRP"

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)

RUNNER="$PROJECT_ROOT/scripts/run_minebridge_frp.sh"
ICON_SRC="$PROJECT_ROOT/resources/icons/minebridge-frp.svg"
APP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
ICON_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/scalable/apps"
DESKTOP_FILE="$APP_DIR/$APP_ID.desktop"
ICON_TARGET="$ICON_DIR/$APP_ID.svg"

quote_exec_arg() {
  local value=$1
  value=${value//\\/\\\\}
  value=${value//\"/\\\"}
  printf '"%s"' "$value"
}

if [[ ! -x "$RUNNER" ]]; then
  chmod +x "$RUNNER"
fi

if [[ ! -f "$ICON_SRC" ]]; then
  printf 'Icon not found: %s\n' "$ICON_SRC" >&2
  exit 1
fi

mkdir -p "$APP_DIR" "$ICON_DIR"
install -m 0644 "$ICON_SRC" "$ICON_TARGET"

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=$APP_NAME
Name[ru]=$APP_NAME
Comment=GUI for Minecraft FRP tunnels
Comment[ru]=GUI для Minecraft-сервера через FRP-туннель
Exec=$(quote_exec_arg "$RUNNER")
Icon=$APP_ID
Terminal=false
Categories=Game;
StartupNotify=true
Keywords=Minecraft;FRP;Tunnel;Server;VPS;
EOF

chmod +x "$DESKTOP_FILE"

desktop_dirs=("$HOME/Desktop" "$HOME/Рабочий стол")
for desktop_dir in "${desktop_dirs[@]}"; do
  if [[ -d "$desktop_dir" ]]; then
    desktop_shortcut="$desktop_dir/$APP_NAME.desktop"
    cp "$DESKTOP_FILE" "$desktop_shortcut"
    chmod +x "$desktop_shortcut"
    if command -v gio >/dev/null 2>&1; then
      gio set "$desktop_shortcut" metadata::trusted true >/dev/null 2>&1 || true
    fi
  fi
done

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$APP_DIR" >/dev/null 2>&1 || true
fi

printf '%s launcher installed.\n' "$APP_NAME"
printf 'Application menu: %s\n' "$DESKTOP_FILE"
printf 'Icon: %s\n' "$ICON_TARGET"
