# MineBridge FRP

> Десктопное приложение, чтобы открыть локальный Minecraft-сервер друзьям через FRP-туннель на дешёвой VPS — без проброса портов, без NAT-плясок, без отдельных консолей и батников.

MineBridge FRP — это:

- **Electron-оболочка** (React + TypeScript + Vite) с тёмной темой, выезжающей консолью и линейным мастером первого запуска.
- **Локальный FastAPI-бэкенд** (FastAPI, SQLAlchemy, Pydantic v2), который Electron поднимает автоматически. В релизных сборках он упакован в отдельный PyInstaller-бинарник, поэтому пользователю не нужен установленный Python.
- **VPS-автоматизация** на paramiko: SSH-проверки, установка `frps`, генерация `frps.toml`, systemd-юнит, открытие портов через `ufw`/`firewalld`.
- **Локальный `frpc`**: токен, конфиг, скачивание зафиксированной версии FRP (`v0.69.1`), запуск/остановка, проверка внешнего порта.
- **Управление Minecraft-сервером**: запуск `.jar`, `.sh`, `.bash`, `.bat`, `.cmd`, `.ps1` без открытия лишних окон. Логи и команды — внутри встроенного xterm-терминала.

## Что нового в текущей версии

### Setup-мастер первого запуска
Вместо 8 разрозненных вкладок — линейный мастер из 4 шагов: **VPS → Туннель → Сервер → Готово**. На каждом шаге всё автосохраняется при изменении полей (debounce 400ms), а единственная большая кнопка делает сразу всю установку:
- "Проверить и установить frps" — `check-ssh → install-frps → firewall/open` за один клик.
- "Скачать frpc и записать конфиг" — `generate-token → save → download → write config` за один клик.
- "Принять EULA и записать server.properties" — `eula.txt + server.properties` сразу.

Состояние мастера живёт на бэкенде (`config_dir/setup.json`), поэтому смена машины или сброс localStorage не возвращает пользователя в начало.

### Главный экран
Одна большая карточка статуса: точка-индикатор, аптайм, число игроков, адрес `host:port` с кнопкой COPY и **один CTA** (Запустить / Остановить). Все редкие действия — в overflow-меню `⋮`. Под карточкой — 4 компактных квик-метрики (CPU / RAM / сеть / игроки) и выезжающая по `~` консоль сервера.

### Sidebar — 4 пункта вместо 8
`Home / Настройка / Логи / Настройки`. Точка-индикатор у "Настройка" зажигается, если мастер не завершён.

### Поддержка скриптов и автодетект
- **`.sh` / `.bat` / `.cmd` / `.ps1`** запускаются через детект OS, без всплывающих консольных окон (`CREATE_NO_WINDOW` на Windows, флаг `nogui` пробрасывается лаунчерам Forge/NeoForge/Paper).
- **Автопоиск файла запуска** — после выбора папки сервера бэкенд сканирует её и предпочитает `run.sh`/`run.bat` поверх известных jar-имён. Скрипт побеждает, потому что у Forge именно он корректно поднимает мод-стек.
- **Автопоиск Java** — обходит `JAVA_HOME`, `PATH`, типичные каталоги (`Program Files\Eclipse Adoptium\*`, `/usr/lib/jvm/*`, `/Library/Java/JavaVirtualMachines/*`, sdkman) и зовёт `-version` для каждой найденной. Если установок несколько — открывается модалка выбора.

## Архитектура

```
┌──────────────────────────────────────┐
│ Electron (main + preload)            │  IPC dialog.showOpenDialog
│  └ React + Vite + TS                 │  Tailwind, framer-motion, xterm
│     └ React Query + zustand          │
└────────────┬─────────────────────────┘
             │ HTTP + WebSocket
             ▼
┌──────────────────────────────────────┐
│ FastAPI 127.0.0.1:47831              │
│  ├ /api/setup/status                 │  ← состояние мастера
│  ├ /api/profiles/{vps,mc,tunnels}    │
│  ├ /api/vps/{check-ssh, install-frps}│
│  ├ /api/frpc/{token, download, ...}  │
│  ├ /api/minecraft/{detect-*, start}  │
│  └ /ws/events                        │
│                                      │
│ services: profile, vps_manager,      │
│ frp_manager, minecraft_manager,      │
│ detection, diagnostics, metrics,     │
│ password_vault, setup_state          │
└──────────────────────────────────────┘
```

База — SQLite (`SQLAlchemy 2`). Пароли VPS — шифрованный vault на `cryptography`. Бэкенд слушает только `127.0.0.1`; в Electron-сессии main process генерирует runtime API token, передаёт его backend через `MINEBRIDGE_API_TOKEN`, а renderer добавляет `X-MineBridge-Token` для HTTP и query-token для WebSocket.

## Стек

- **Frontend**: Electron 33, Vite 6, React 18, TypeScript 5, zustand, @tanstack/react-query, framer-motion, recharts, @xterm/xterm, lucide-react, tailwindcss.
- **Backend**: FastAPI, uvicorn, SQLAlchemy 2, Pydantic 2, paramiko, tomlkit, cryptography, psutil, platformdirs.
- **Release backend bundle**: PyInstaller one-file executable in `resources/backend-bin/`.

## Требования

- Python 3.11+ (только для разработки и сборки; пользователям релизного installer Python не нужен)
- Node.js 18+ и npm
- Windows 10/11 или Linux x86_64
- Java 17+ (для запуска самого Minecraft-сервера; внутри приложения её можно автоматически найти)
- VPS с Linux x86_64 и SSH (для размещения `frps`)

## Установка для разработки

```bash
python -m venv .venv
source .venv/bin/activate         # Windows: .\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
npm install
```

## Запуск

Полностью (Electron + бэкенд):

```bash
npm run dev          # dev-режим: Vite + Electron live-reload
# или после установки python-пакета:
minebridge-frp       # production-shell
```

Только бэкенд (полезно для отладки API):

```bash
minebridge-frp-api
```

## Сборка

Renderer (для разработки):

```bash
npm run build        # tsc --noEmit + vite build → dist-electron/renderer/
npm run build:backend # PyInstaller → dist-backend/minebridge-frp-api(.exe)
```

### Сборка установщика (npm package)

Для дистрибуции используется [electron-builder](https://www.electron.build/). Команды:

```bash
npm install          # один раз
npm run dist         # сборка под текущую ОС
npm run dist:win     # NSIS .exe + portable .exe (только под Windows)
npm run dist:linux   # AppImage + .deb (только под Linux)
npm run dist:dir     # без архива — папка с готовым приложением для отладки
```

Артефакты появятся в `dist-installer/`:

- **Windows**: `MineBridge-FRP-<version>-x64.exe` (NSIS-инсталлятор) + `MineBridge-FRP-<version>-x64.exe` (portable).
- **Linux**: `MineBridge-FRP-<version>-x64.AppImage` (запускается двойным кликом) + `MineBridge-FRP-<version>-x64.deb`.

Иконки лежат в [`resources/icons/`](resources/icons/): `icon.ico` для Windows и `icon.png` 512×512 для Linux. Перегенерировать их из текущего векторного стиля можно командой:

```bash
python scripts/generate_icons.py
```

### Что делает первый запуск установленного приложения

Установщик содержит Electron + UI и готовый backend executable в `resources/backend-bin/`. При старте:

1. Electron генерирует случайный API token для текущей сессии.
2. Запускает `resources/backend-bin/minebridge-frp-api(.exe)` с `MINEBRIDGE_API_TOKEN`.
3. Передаёт token renderer через preload (`window.minebridge.apiToken`).
4. Renderer обращается к backend только с этим token.

Fallback через пользовательский Python и `pip install --user` оставлен только для dev/старых unpacked-сборок, где `backend-bin` отсутствует.

### GitHub Releases

Релизный workflow в [`.github/workflows/release.yml`](.github/workflows/release.yml). Срабатывает на push тега `v*.*.*`:

```bash
npm version <version> --no-git-tag-version
# вручную синхронизировать pyproject.toml и minebridge_frp/__init__.py
python -m ruff check minebridge_frp tests scripts
python -m pytest tests -q
npm run build

git commit -am "Release v<version>"
git tag v<version>
git push origin main --tags
```

Action собирает Windows и Linux installer в параллельных matrix-job (`ubuntu-22.04` + `windows-latest`): ставит Python dev dependencies, прогоняет ruff + pytest, собирает renderer, собирает bundled backend через PyInstaller, запускает electron-builder, аплоадит артефакты и публикует их в GitHub Releases с автоматически сгенерированным changelog'ом из коммитов. Никаких секретов кроме встроенного `GITHUB_TOKEN` не требуется.

Можно также запустить вручную через "Run workflow" во вкладке Actions без создания тега — артефакты тогда положатся в `Actions → Artifacts`, но релиз создан не будет.

## Тесты

```bash
python -m ruff check minebridge_frp tests scripts
python -m pytest tests -q
npm run build
```

В CI пайплайне 66 тестов + 1 skipped. Ruff line-length 100, pyproject targets py311 (`E/F/I/UP/B`).

## Linux desktop-launcher

```bash
scripts/install_desktop_launcher.sh
```

Создаст пункт `MineBridge FRP` в меню приложений, использующий `.venv` через `scripts/run_minebridge_frp.sh`.

## Безопасность сборок

В дистрибутивные артефакты **не должны** попадать:
- `.minebridge-frp/` (профили и состояние мастера)
- SQLite-базы и экспорты профилей
- скачанные FRP-архивы/бинарники
- `dist-backend/`, `dist-electron/`, `dist-installer/`, `build/`
- `.env`, SSH-ключи, пароли

## Структура проекта

```
electron/
├── main.cjs          Electron main process + IPC for native dialogs
└── preload.cjs       contextBridge: window.minebridge

frontend/src/
├── App.tsx
├── components/
│   ├── layout/       AppShell, Sidebar
│   ├── setup/        StepNav, VpsStep, TunnelStep, ServerStep, DoneStep
│   └── ui/           Card, Button, Console, ConsoleDrawer, OverflowMenu, JavaPicker, ...
├── screens/          HomeScreen, SetupScreen, LogsScreen, SettingsScreen
├── lib/              api, dialog, useDebouncedSave, types
└── store/            zustand: setupStatus, consoleOpen, минимальный runtime state

minebridge_frp/app/
├── api/              FastAPI factory, schemas, runtime, events
├── core/             AppContext, paths, exceptions, logger
├── db/               SQLAlchemy models, migrations
├── models/           Pydantic: setup, profile, minecraft, tunnel, vps, diagnostics
├── services/         profile, vps_manager, frp_manager, minecraft_manager,
│                     detection, diagnostics, metrics, password_vault, setup_state
└── utils/            archive, ports, secrets, process, ...

tests/                pytest, 66 кейсов
docs/                 миграция Qt → Electron (этапы 1–10)
scripts/              run/install скрипты для Linux, generate_icons.py
```

## Roadmap

- Health-точки в sidebar для VPS / туннеля / Minecraft (P2).
- Slim-mode tray-окно в стиле Tailscale (P3).
- Подписанные установщики и автообновление `frps`/`frpc`.
- Richer remote diagnostics (latency, версия `frps`, размер логов).

## Лицензия

MIT.
