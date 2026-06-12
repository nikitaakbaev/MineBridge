# Electron migration: этапы 4-5

Дата выполнения: 2026-06-13.

## Цель

Этап 4: создать Electron-приложение, поднять React-интерфейс и базовую навигацию.

Этап 5: перенести основные экраны в новый frontend:

- Dashboard;
- Servers;
- Minecraft;
- Tunnels;
- VPS;
- Diagnostics;
- Logs;
- Settings.

## Что создано

Electron shell:

- `electron/main.cjs`
- `electron/preload.cjs`

Frontend/Vite:

- `package.json`
- `tsconfig.json`
- `vite.config.ts`
- `tailwind.config.ts`
- `postcss.config.cjs`
- `frontend/index.html`
- `frontend/src/main.tsx`
- `frontend/src/App.tsx`
- `frontend/src/styles.css`

React app:

- `frontend/src/components/layout/AppShell.tsx`
- `frontend/src/components/layout/Sidebar.tsx`
- `frontend/src/components/ui/Button.tsx`
- `frontend/src/components/ui/Card.tsx`
- `frontend/src/components/ui/Field.tsx`
- `frontend/src/components/ui/ProfilePicker.tsx`
- `frontend/src/components/ui/ScreenHeader.tsx`
- `frontend/src/components/ui/StatusBadge.tsx`
- `frontend/src/components/ui/TerminalConsole.tsx`
- `frontend/src/hooks/useBackendEvents.ts`
- `frontend/src/lib/api.ts`
- `frontend/src/lib/cn.ts`
- `frontend/src/lib/types.ts`
- `frontend/src/store/app-store.ts`

Screens:

- `frontend/src/screens/DashboardScreen.tsx`
- `frontend/src/screens/ServersScreen.tsx`
- `frontend/src/screens/MinecraftScreen.tsx`
- `frontend/src/screens/TunnelsScreen.tsx`
- `frontend/src/screens/VpsScreen.tsx`
- `frontend/src/screens/DiagnosticsScreen.tsx`
- `frontend/src/screens/LogsScreen.tsx`
- `frontend/src/screens/SettingsScreen.tsx`

## Архитектура

Electron main process:

- обеспечивает single-instance lock через `app.requestSingleInstanceLock()`;
- запускает Python backend командой `python3 -m minebridge_frp.app.api.main`;
- открывает React renderer.

React renderer:

- не содержит SSH, FRP, Minecraft или database логики;
- использует `fetch` к `http://127.0.0.1:47831`;
- слушает `ws://127.0.0.1:47831/ws/events`;
- хранит только UI-состояние, runtime statuses и последние строки логов.

Python backend:

- остается владельцем профилей, БД, SSH, FRP, Minecraft process lifecycle и диагностики.

## Используемый frontend stack

Добавлен проектный стек:

- Electron;
- React;
- TypeScript;
- Vite;
- TailwindCSS;
- shadcn-style локальные UI components;
- Framer Motion;
- Lucide Icons;
- Zustand;
- React Query;
- xterm.js;
- Recharts.

## Что уже работает на уровне кода

- Electron shell запускает Python backend и renderer.
- React app имеет launcher-like layout с sidebar.
- Dashboard показывает активную конфигурацию, адрес подключения и большую кнопку запуска.
- Servers показывает текущую сборку Minecraft/VPS/tunnel.
- Minecraft screen редактирует профиль, запускает/останавливает сервер и отправляет команды через API.
- Tunnels screen редактирует frpc-профиль, создает конфиг, скачивает frpc, стартует/останавливает frpc.
- VPS screen редактирует VPS-профиль и вызывает SSH/frps endpoints.
- Diagnostics вызывает Python diagnostics API.
- Logs показывает app/Minecraft/frpc logs через xterm.js.
- Settings показывает текущее окружение Electron/Python/SQLite.

## Что еще использует PySide6

Старый UI пока не удален:

- `minebridge_frp/app/main.py`
- `minebridge_frp/app/ui/**`
- `minebridge_frp/app/core/single_instance.py`
- `tests/test_ui_behaviour.py`

Это будет удаляться или отключаться на этапах 6-7 после проверки Electron UI.

## Что можно удалить после завершения миграции

После этапа 7:

- старые Qt tabs/widgets/theme/layout helpers;
- Qt single-instance helper;
- Qt launcher scripts, если Electron packaging заменит их;
- PyInstaller spec под PySide6;
- `PySide6` из Python dependencies;
- UI-тесты, завязанные на Qt.

## Как запускать после установки Node

Python backend dependencies:

```bash
pip install -e ".[dev]"
```

Node dependencies:

```bash
npm install
```

Electron development:

```bash
npm run dev
```

Renderer build:

```bash
npm run build
```

## Ограничение текущей проверки

В текущем окружении нет `node` и `npm`, поэтому Electron frontend не был собран локально. Python checks остаются доступными.
