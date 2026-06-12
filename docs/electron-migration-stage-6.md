# Electron migration: этап 6

Дата выполнения: 2026-06-13.

## Цель

Заменить старый PySide6 UI новым Electron UI как основной пользовательский интерфейс.

На этом этапе Qt-код еще не удаляется. Он остается временным fallback до этапа 7.

## Что изменено

Создан основной launcher:

- `minebridge_frp/app/electron_launcher.py`

Изменены entry points:

- `minebridge-frp` теперь запускает Electron UI;
- `minebridge-frp-qt` запускает старый PySide6 UI;
- `minebridge-frp-api` по-прежнему запускает Python FastAPI backend.

Изменен desktop runner:

- `scripts/run_minebridge_frp.sh`

Теперь Linux app-menu ярлык использует Electron path через `minebridge-frp`.

## Как запускается приложение

Основной путь:

```bash
minebridge-frp
```

или через установленный desktop launcher.

Что происходит:

1. Python entry point проверяет наличие Electron/Vite файлов.
2. Проверяет наличие `npm`.
3. Запускает `npm run dev`.
4. Electron main process запускает Python backend:

```bash
python3 -m minebridge_frp.app.api.main
```

5. React renderer открывает UI и общается с backend через localhost API/WebSocket.

## Временный Qt fallback

До этапа 7 старый UI доступен явно:

```bash
minebridge-frp-qt
```

или:

```bash
MINEBRIDGE_USE_QT=1 minebridge-frp
```

Этот fallback нужен только на время стабилизации Electron UI.

## Что уже работает

- Electron UI стал основным launch path.
- Старый desktop launcher теперь ведет в Electron launcher.
- Qt UI больше не является default entry point.
- Python backend остается владельцем бизнес-логики.
- Electron main process отвечает за single-instance поведение.
- `npm install` создает `package-lock.json`.
- `npm run build` успешно собирает React renderer.
- Launcher очищает `ELECTRON_RUN_AS_NODE` и `ELECTRON_NO_ATTACH_CONSOLE` перед запуском npm.

## Что все еще использует PySide6

- `minebridge_frp/app/main.py`;
- `minebridge_frp/app/ui/**`;
- `minebridge_frp/app/core/single_instance.py`;
- `tests/test_ui_behaviour.py`;
- dependency `PySide6` в `pyproject.toml`.

Это удаляется на этапе 7.

## Что можно удалить после этапа 7

- `minebridge-frp-qt` entry point;
- `MINEBRIDGE_USE_QT` fallback;
- PySide6 dependency;
- старый Qt UI package;
- PyInstaller spec под Qt;
- Qt-specific desktop behavior.

## Ограничение проверки

Node.js/npm установлены, зависимости поставлены, renderer build прошел.
Полноценный GUI-запуск Electron в текущей среде упирается в Linux sandbox:

```text
sandbox_host_linux.cc Check failed: shutdown: Operation not permitted
```

Это ограничение текущей среды выполнения, а не TypeScript/Vite build.
