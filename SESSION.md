# MineBridge FRP Session Export

Date: 2026-06-27

## What was completed

- Fixed the installer/backend startup path by bundling the Python backend.
- Added local API token protection between Electron and the FastAPI backend.
- Fixed launcher detection priority for Forge-style `run.sh` / `run.bat`.
- Updated release metadata and published `v0.1.3`.
- Reworked the frontend visual system into a denser industrial/terminal style.
- Removed the false `Failed to fetch` setup crash during backend startup.
- Fixed CORS/token handling so `OPTIONS` preflight is not rejected with `403 Forbidden`.
- Started work on bundling FRP binaries to avoid runtime downloads.

## Current FRP source

Official FRP release used by the app:

- `https://api.github.com/repos/fatedier/frp/releases/tags/v0.69.1`
- Windows asset:
  `https://github.com/fatedier/frp/releases/download/v0.69.1/frp_0.69.1_windows_amd64.zip`
- Linux asset:
  `https://github.com/fatedier/frp/releases/download/v0.69.1/frp_0.69.1_linux_amd64.tar.gz`

## Current code changes in progress

- Added `scripts/prepare_frpc_bundle.py` to pre-download official FRP binaries.
- Added `minebridge_frp/app/utils/bundled_assets.py`.
- Updated `minebridge_frp/app/services/download_service.py` to prefer bundled `frpc`.
- Updated `minebridge_frp/app/services/frp_manager.py` to prefer bundled `frpc`.
- Updated `minebridge_frp/app/services/vps_manager.py` to prefer bundled `frps`.
- Updated `package.json` to include `resources/frp-bundled` in installer assets.
- Updated `.github/workflows/release.yml` to run `npm run prepare:frpc`.

## Why this matters

Runtime download of `frpc.exe` is what often triggers Windows Defender / SmartScreen.
Bundling the binary inside the installer is the practical next step to reduce
false positives. Signing the installer is still the long-term fix.

## Validation already run

- `npm run build`
- Python syntax check for the edited backend/scripts files

## Useful commands

```powershell
npm run dev
python scripts/prepare_frpc_bundle.py --version v0.69.1
npm run build
```

## Open items

- Generate and ship the bundled FRP binaries.
- Rebuild the installer and test Defender behavior.
- Sign the Windows installer/binary to reduce SmartScreen warnings.
- Continue bundle-size cleanup for the renderer.
