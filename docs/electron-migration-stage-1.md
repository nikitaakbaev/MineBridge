# Electron migration: этап 1

Дата анализа: 2026-06-13.

Цель этапа 1: зафиксировать текущую архитектуру PySide6-приложения, построить карту UI, сервисов, моделей и зависимостей, а также выбрать базовую схему миграции на Electron + React + TypeScript без переноса бизнес-логики из Python.

## Итоговое решение

Для связи нового Electron UI с существующим Python backend выбирается локальный FastAPI API с WebSocket-каналом.

Причины:

- HTTP endpoints хорошо подходят для команд, CRUD профилей, диагностики, настроек и разовых операций.
- WebSocket нужен для потоковых событий: логи Minecraft, логи frpc, прогресс установки FRP на VPS, статусы процессов и диагностики.
- Python-сервисы остаются единственным источником бизнес-логики.
- React не получает SSH, FRP, Minecraft process management или работу с БД напрямую.

Целевая схема:

```text
Electron main process
  запускает Python backend
      |
      v
React + TypeScript UI
  HTTP/WebSocket localhost
      |
      v
FastAPI app
      |
      v
Python services, models, database
```

## Текущая карта UI

Активный вход в приложение:

- `minebridge_frp/app/main.py`
  - создает `QApplication`;
  - создает `AppContext`;
  - настраивает логирование;
  - включает `SingleInstanceGuard`;
  - открывает `MainWindow`.

Главное окно:

- `minebridge_frp/app/ui/main_window.py`
  - `MainWindow(QMainWindow)`;
  - хранит `ProfileService`;
  - создает вкладки;
  - восстанавливает геометрию окна через `QSettings`;
  - управляет tray icon и поведением закрытия.

Активные вкладки в `MainWindow`:

- `VpsTab`
  - файл: `minebridge_frp/app/ui/tabs/vps_tab.py`;
  - назначение: VPS-профили, SSH, установка frps, systemd, firewall, status;
  - использует: `ProfileService`, `PasswordVault`, `VpsManager`, `run_in_thread`;
  - UI-состояние: поля SSH, auth type, install dir, frps port, dashboard, лог-окно.

- `MinecraftTab`
  - файл: `minebridge_frp/app/ui/tabs/minecraft_tab.py`;
  - назначение: локальный Minecraft server config, EULA, server.properties, запуск/остановка процесса, консоль команд;
  - использует: `ProfileService`, `MinecraftManager`;
  - UI-состояние: server dir, jar, java path, RAM, port, version, server.properties, логи.

- `FrpcTab`
  - файл: `minebridge_frp/app/ui/tabs/tunnel_tab.py`;
  - назначение: локальный frpc config, token, download, start/stop, external port check;
  - использует: `ProfileService`, `FrpManager`, `DownloadService` через manager;
  - UI-состояние: local/remote ports, server addr, token, frpc folder, логи.

- `DiagnosticsTab`
  - файл: `minebridge_frp/app/ui/tabs/diagnostics_tab.py`;
  - назначение: диагностика активной конфигурации;
  - использует: `DiagnosticsService`, `ProfileService`, `run_in_thread`;
  - UI-состояние: таблица результатов, отчет, fix actions.

- `LogsTab`
  - файл: `minebridge_frp/app/ui/tabs/logs_tab.py`;
  - назначение: просмотр логов приложения;
  - использует: файловую систему и `LogViewer`;
  - UI-состояние: вкладки с фильтрами логов.

- `SettingsTab`
  - файл: `minebridge_frp/app/ui/tabs/settings_tab.py`;
  - назначение: настройки интерфейса и поведения закрытия;
  - использует: `QSettings`, `AppContext`;
  - UI-состояние: paths, language placeholder, close behavior, timeout placeholder.

Неактивный/устаревший UI:

- `minebridge_frp/app/ui/tabs/quick_start_tab.py`
  - файл существует, но `MainWindow` больше не подключает эту вкладку;
  - содержит старый all-in-one сценарий запуска;
  - при миграции его лучше использовать только как историческую справку для будущего Electron Dashboard, а не переносить напрямую.

Общие UI-компоненты:

- `minebridge_frp/app/ui/layouts.py`
  - `FlowLayout`, `scroll_panel`, `profile_selector_panel`, `prepare_action_button`;
- `minebridge_frp/app/ui/theme.py`
  - темная Qt stylesheet;
- `minebridge_frp/app/ui/workers.py`
  - `QThread` wrapper для фоновых операций;
- `minebridge_frp/app/ui/widgets/log_viewer.py`
  - Qt-лог-окно;
- `minebridge_frp/app/ui/widgets/console_input.py`
  - Qt-командная строка;
- `minebridge_frp/app/ui/widgets/path_picker.py`
  - Qt file/folder picker;
- `minebridge_frp/app/ui/widgets/status_badge.py`
  - Qt status label;
- `minebridge_frp/app/ui/icons.py`
  - загрузка `QIcon`.

## Текущая карта сервисов

Сервисы, которые уже в основном подходят для backend API:

- `ProfileService`
  - файл: `minebridge_frp/app/services/profile_service.py`;
  - назначение: high-level API профилей, import/export, активные VPS/Minecraft/frpc профили;
  - зависимости: `AppContext`, SQLAlchemy repository, Pydantic models;
  - Qt-зависимостей нет.

- `VpsManager`
  - файл: `minebridge_frp/app/services/vps_manager.py`;
  - назначение: SSH, remote commands, SFTP upload, frps install/config/systemd/firewall/status;
  - зависимости: `paramiko`, `DownloadService`, `firewall_service`, `systemd_service`, `create_frps_toml`;
  - Qt-зависимостей нет.

- `DownloadService`
  - файл: `minebridge_frp/app/services/download_service.py`;
  - назначение: получение FRP release asset, скачивание, распаковка;
  - зависимости: `requests`, archive utils, platform detection;
  - Qt-зависимостей нет.

- `PasswordVault`
  - файл: `minebridge_frp/app/services/password_vault.py`;
  - назначение: локальное шифрование/расшифровка сохраненного SSH password;
  - зависимости: `cryptography`;
  - Qt-зависимостей нет.

- `DiagnosticsService`
  - файл: `minebridge_frp/app/services/diagnostics_service.py`;
  - назначение: проверки активного профиля;
  - зависимость от Qt косвенная, потому что создает `MinecraftManager` и `FrpManager`.

- `firewall_service.py`
  - shell-команды для ufw/firewalld;
- `systemd_service.py`
  - генерация systemd unit для frps.

Сервисы, которые надо отделить от Qt на этапе 2:

- `MinecraftManager`
  - файл: `minebridge_frp/app/services/minecraft_manager.py`;
  - проблемы: наследуется от `QObject`, использует `QProcess`, `Signal`, `QDesktopServices`, `QUrl`;
  - что оставить: Java discovery/version check, server.properties, EULA file operations, process lifecycle, command stdin, log stream;
  - целевая форма: обычный Python-класс + отдельный process runner на `subprocess.Popen`/async task + callbacks/event bus.

- `FrpManager`
  - файл: `minebridge_frp/app/services/frp_manager.py`;
  - проблемы: наследуется от `QObject`, использует `QProcess`, `Signal`;
  - что оставить: генерация frps/frpc TOML, download/find binary, start/stop frpc, log stream, port check;
  - целевая форма: обычный Python-класс + process runner.

Qt-only runtime helpers:

- `SingleInstanceGuard`
  - файл: `minebridge_frp/app/core/single_instance.py`;
  - использует `QLockFile`, `QLocalServer`, `QLocalSocket`, `QObject`, `Signal`;
  - после Electron миграции должен перейти в Electron main process или в отдельный Python lock helper без Qt.

## Текущая карта моделей

Pydantic-модели:

- `Profile`
  - metadata: id, name, created_at, updated_at, is_default;
- `ProfileBundle`
  - legacy/exportable связка `Profile + VpsConfig + MinecraftConfig + TunnelConfig`;
- `VpsProfileBundle`
  - независимый VPS preset;
- `MinecraftProfileBundle`
  - независимый Minecraft preset;
- `TunnelProfileBundle`
  - независимый frpc preset;
- `VpsConfig`
  - SSH host/port/user/auth, encrypted password field, private key, install dir, frps/dashboard ports;
- `MinecraftConfig`
  - server dir, jar, java, RAM, port, server type/version, server.properties values;
- `TunnelConfig`
  - local IP/port, remote port, protocol, frp server addr/bind port, token, auto start;
- `DiagnosticResult`
  - status/name/description/fix metadata.

Эти модели пригодны как DTO для FastAPI. Для Electron/React нужно будет сгенерировать или вручную описать TypeScript-типы на их основе.

## Текущая карта БД

Файлы:

- `minebridge_frp/app/db/database.py`;
- `minebridge_frp/app/db/repositories.py`;
- `minebridge_frp/app/db/migrations.py`.

Текущие таблицы:

- legacy bundle:
  - `profiles`;
  - `vps_configs`;
  - `minecraft_configs`;
  - `tunnel_configs`;
- независимые профили:
  - `vps_profiles`;
  - `minecraft_profiles`;
  - `tunnel_profiles`.

Repository API уже подходит для backend-слоя, потому что UI работает через `ProfileService`, а не напрямую через SQLAlchemy.

## Зависимости и границы

Python-зависимости проекта сейчас:

- UI: `PySide6`;
- SSH: `paramiko`;
- config generation: `tomlkit`;
- validation/DTO: `pydantic`;
- DB: `SQLAlchemy`;
- runtime utilities: `psutil`, `requests`, `platformdirs`;
- secrets: `cryptography`.

Зависимости, которые должны остаться в backend:

- `paramiko`;
- `tomlkit`;
- `pydantic`;
- `SQLAlchemy`;
- `psutil`;
- `requests`;
- `platformdirs`;
- `cryptography`.

Зависимости, которые должны уйти из backend перед этапом 3:

- `PySide6.QtCore.QObject`;
- `PySide6.QtCore.QProcess`;
- `PySide6.QtCore.Signal`;
- `PySide6.QtGui.QDesktopServices`;
- `PySide6.QtCore.QUrl`.

PySide6 может временно оставаться только в старом UI до этапа 7.

## Основные текущие потоки данных

VPS:

```text
VpsTab
  -> VpsConfig from form
  -> PasswordVault
  -> VpsManager
  -> Paramiko SSH/SFTP
  -> remote frps/systemd/firewall
  -> LogViewer/status messages
```

Minecraft:

```text
MinecraftTab
  -> MinecraftConfig from form
  -> MinecraftManager
  -> Java/server.jar/eula/server.properties
  -> QProcess Java server
  -> LogViewer + ConsoleInput
```

frpc:

```text
FrpcTab
  -> TunnelConfig from form
  -> FrpManager
  -> frpc.toml + downloaded frpc binary
  -> QProcess frpc
  -> LogViewer/status messages
```

Diagnostics:

```text
DiagnosticsTab
  -> ProfileService.get_active_configuration()
  -> DiagnosticsService
  -> MinecraftManager + FrpManager + ports/process utils
  -> DiagnosticResult[]
  -> table/report/fix actions
```

Profiles:

```text
Tabs
  -> ProfileService
  -> ProfileRepository
  -> SQLAlchemy records
  -> SQLite
```

## Предлагаемый API-контур для этапа 3

HTTP endpoints:

- `GET /api/health`;
- `GET /api/profiles/active`;
- `GET /api/profiles/vps`;
- `POST /api/profiles/vps`;
- `PATCH /api/profiles/vps/{id}`;
- `DELETE /api/profiles/vps/{id}`;
- аналогично для `minecraft` и `tunnels`;
- `POST /api/vps/check-ssh`;
- `POST /api/vps/install-frps`;
- `POST /api/vps/frps/config`;
- `POST /api/vps/frps/start`;
- `POST /api/vps/frps/stop`;
- `POST /api/vps/frps/restart`;
- `GET /api/vps/frps/status`;
- `POST /api/vps/firewall/open`;
- `POST /api/minecraft/server-properties`;
- `POST /api/minecraft/start`;
- `POST /api/minecraft/stop`;
- `POST /api/minecraft/restart`;
- `POST /api/minecraft/command`;
- `POST /api/frpc/config`;
- `POST /api/frpc/download`;
- `POST /api/frpc/start`;
- `POST /api/frpc/stop`;
- `POST /api/frpc/check-port`;
- `POST /api/diagnostics/run`;
- `GET /api/logs/app`.

WebSocket channels:

- `/ws/events`;
  - process status changes;
  - Minecraft logs;
  - frpc logs;
  - VPS action output/progress;
  - diagnostics progress.

## Что уже готово для миграции

- Бизнес-модели уже описаны через Pydantic.
- Профили отделены от UI через `ProfileService`.
- БД скрыта за repository/service layer.
- VPS manager уже не зависит от Qt.
- Большая часть генерации конфигов и проверок оформлена как обычный Python.
- Тесты покрывают модели, профили, FRP/Minecraft helpers, ports, diagnostics.

## Что все еще использует PySide6

- Весь старый UI в `minebridge_frp/app/ui/**`.
- Entry point `minebridge_frp/app/main.py`.
- `MinecraftManager` и `FrpManager`.
- `DiagnosticsService` косвенно зависит от Qt через эти менеджеры.
- `SingleInstanceGuard`.
- Тесты UI в `tests/test_ui_behaviour.py`.

## Что можно удалить только после завершения миграции

Не удалять сейчас. После этапа 7 можно будет удалить:

- `minebridge_frp/app/ui/**`;
- Qt entry point `minebridge_frp/app/main.py` или заменить его backend entry point;
- `tests/test_ui_behaviour.py`;
- PyInstaller desktop packaging для Qt, если будет заменено Electron packaging;
- `PySide6` из `pyproject.toml`;
- Qt launcher scripts, если Electron installer возьмет их роль.

## План этапа 2

На следующем этапе нужно отделить бизнес-логику от UI:

1. Создать backend process runner без Qt.
   - Поддержать start/stop/kill/stdin.
   - Поддержать поток stdout/stderr через callback или event emitter.
   - Покрыть тестами без GUI.

2. Переписать `MinecraftManager`.
   - Убрать `QObject`, `Signal`, `QProcess`, `QDesktopServices`, `QUrl`.
   - `open_eula` должен только создавать/возвращать путь; открытие файла останется обязанностью UI/API клиента.

3. Переписать `FrpManager`.
   - Убрать `QObject`, `Signal`, `QProcess`.
   - Оставить генерацию конфигов, download, find binary, start/stop, log callbacks.

4. Обновить старый PySide6 UI как временный клиент.
   - Вместо Qt signals подключить callbacks новых managers.
   - Не ломать текущую работоспособность до появления Electron UI.

5. Обновить `DiagnosticsService`.
   - Убедиться, что диагностика больше не создает Qt-объекты.

6. Проверить тесты.
   - `python -m compileall minebridge_frp tests`;
   - `ruff check .`;
   - `pytest`.

## Артефакты этапа 1

Создан документ:

- `docs/electron-migration-stage-1.md`.

Изменений в бизнес-логике на этапе 1 нет.
