# Electron migration: этап 7

Дата выполнения: 2026-06-13.

## Цель

Удалить остатки Qt-интерфейса. Python должен остаться только backend-слоем для Electron UI.

## Что удалено

Удален старый PySide6 entry point:

- `minebridge_frp/app/main.py`

Удален Qt single-instance helper:

- `minebridge_frp/app/core/single_instance.py`

Удален старый Qt UI package:

- `minebridge_frp/app/ui/**`

Удалены Qt UI tests:

- `tests/test_ui_behaviour.py`

Удалена PyInstaller packaging-схема старого Qt-приложения:

- `packaging/minebridge-frp.spec`
- `scripts/build_linux.sh`
- `scripts/build_windows.ps1`

## Что изменено

`pyproject.toml`:

- удалена dependency `PySide6`;
- удален entry point `minebridge-frp-qt`;
- `minebridge-frp` остается Electron launcher;
- `minebridge-frp-api` остается backend API launcher.

`scripts/run_minebridge_frp.sh`:

- удален `MINEBRIDGE_USE_QT` fallback;
- скрипт запускает только Electron launcher.

`minebridge_frp/app/electron_launcher.py`:

- удалена логика импорта старого Qt entry point;
- если npm отсутствует, launcher показывает инструкцию без предложения Qt fallback.

## Что теперь является основным приложением

Desktop UI:

```bash
minebridge-frp
```

Backend API:

```bash
minebridge-frp-api
```

Electron main process запускает Python backend, а React renderer работает через localhost API/WebSocket.

## Что уже работает

- В Python-коде больше нет импортов PySide6.
- В project scripts больше нет `minebridge-frp-qt`.
- Старый Qt UI удален из дерева проекта.
- Electron UI остается единственным desktop UI.
- Python backend остается владельцем бизнес-логики.

## Что еще можно улучшить дальше

- Добавить production Electron packaging вместо старого PyInstaller.
- Разделить frontend bundle на chunks, чтобы убрать Vite warning о большом JS chunk.
- Добавить Playwright smoke-test для renderer после настройки GUI-capable окружения.
- Добавить автоматический запуск backend из packaged Electron build без зависимости от development checkout.
