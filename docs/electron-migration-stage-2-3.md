# Electron migration: этапы 2-3

Дата выполнения: 2026-06-13.

## Цель

Этап 2: отделить бизнес-логику от PySide6.

Этап 3: создать локальный FastAPI backend для будущего Electron + React frontend.

## Что изменено

### Backend process runtime

Созданы:

- `minebridge_frp/app/services/events.py`
- `minebridge_frp/app/services/process_runner.py`

Теперь долгоживущие процессы запускаются через чистый Python `subprocess.Popen`, а не через `QProcess`.

`ProcessRunner` поддерживает:

- запуск процесса;
- поток stdout/stderr;
- отправку строки в stdin;
- terminate/kill;
- статус `is_running`;
- callback-события `output`, `started`, `finished`, `error`.

### MinecraftManager

Изменен:

- `minebridge_frp/app/services/minecraft_manager.py`

Убрано из бизнес-сервиса:

- `QObject`;
- `QProcess`;
- `Signal`;
- `QDesktopServices`;
- `QUrl`.

`open_eula()` больше не открывает файл через Qt. Backend только создает `eula.txt` и возвращает путь. Открытие файла осталось обязанностью UI-клиента.

### FrpManager

Изменен:

- `minebridge_frp/app/services/frp_manager.py`

Убрано из бизнес-сервиса:

- `QObject`;
- `QProcess`;
- `Signal`.

Локальный `frpc` теперь запускается через `ProcessRunner`.

### Временная совместимость PySide6 UI

Изменены:

- `minebridge_frp/app/ui/workers.py`
- `minebridge_frp/app/ui/tabs/minecraft_tab.py`
- `minebridge_frp/app/ui/tabs/tunnel_tab.py`

Добавлен `GuiStringBridge`, который безопасно доставляет callback-события backend-сервисов в Qt GUI thread.

Старый PySide6 UI продолжает работать как временный клиент до замены на Electron.

## FastAPI слой

Созданы:

- `minebridge_frp/app/api/__init__.py`
- `minebridge_frp/app/api/app.py`
- `minebridge_frp/app/api/events.py`
- `minebridge_frp/app/api/main.py`
- `minebridge_frp/app/api/runtime.py`
- `minebridge_frp/app/api/schemas.py`

Добавлена команда:

```bash
minebridge-frp-api
```

Она запускает локальный backend API на:

```text
127.0.0.1:47831
```

Добавлены зависимости:

- `fastapi`;
- `uvicorn[standard]`.

## Что экспортирует API

Профили:

- `GET /api/profiles/active`
- `GET /api/profiles/vps`
- `GET /api/profiles/vps/active`
- `POST /api/profiles/vps`
- `POST /api/profiles/vps/{profile_id}/active`
- `PATCH /api/profiles/vps/{profile_id}`
- `PATCH /api/profiles/vps/{profile_id}/name`
- `DELETE /api/profiles/vps/{profile_id}`
- аналогичные endpoints для `minecraft` и `tunnels`.

VPS/frps:

- `POST /api/vps/check-ssh`
- `POST /api/vps/install-frps`
- `POST /api/vps/frps/config`
- `POST /api/vps/frps/start`
- `POST /api/vps/frps/stop`
- `POST /api/vps/frps/restart`
- `POST /api/vps/frps/status`
- `POST /api/vps/firewall/open`

Minecraft:

- `POST /api/minecraft/server-properties`
- `POST /api/minecraft/start`
- `POST /api/minecraft/stop`
- `POST /api/minecraft/restart`
- `POST /api/minecraft/command`

frpc:

- `POST /api/frpc/config`
- `POST /api/frpc/download`
- `POST /api/frpc/start`
- `POST /api/frpc/stop`
- `POST /api/frpc/check-port`

Diagnostics/logs:

- `POST /api/diagnostics/run`
- `GET /api/logs/app`

Events:

- `WS /ws/events`

События уже публикуются для:

- `minecraft.log`;
- `minecraft.status`;
- `minecraft.error`;
- `frpc.log`;
- `frpc.status`;
- `frpc.error`;
- `vps.action`.

## Что уже работает

- `MinecraftManager` и `FrpManager` больше не зависят от PySide6.
- Старый PySide6 UI адаптирован к новым callback-событиям.
- FastAPI app factory создается отдельно от Qt.
- API использует существующие `ProfileService`, `VpsManager`, `MinecraftManager`, `FrpManager`, `DiagnosticsService`.
- WebSocket event bus готов для Electron UI.
- Pydantic-модели используются как response/request DTO.

## Что все еще использует PySide6

- `minebridge_frp/app/main.py`
- `minebridge_frp/app/ui/**`
- `minebridge_frp/app/core/single_instance.py`
- `tests/test_ui_behaviour.py`

Это временно: старый UI остается рабочим клиентом до этапов 4-6.

## Что можно удалить после завершения миграции

После этапа 7:

- старый Qt UI в `minebridge_frp/app/ui/**`;
- Qt entry point `minebridge_frp/app/main.py`;
- `SingleInstanceGuard`, если single-instance будет полностью в Electron main process;
- `PySide6` из зависимостей;
- PyInstaller packaging под Qt;
- UI-тесты, завязанные на PySide6.

## Проверки

Добавлены тесты:

- `tests/test_process_runner.py`
- `tests/test_backend_separation.py`
- `tests/test_api_smoke.py`

`test_api_smoke.py` пропускается, если в текущем окружении еще не установлены `fastapi`/`httpx`.
