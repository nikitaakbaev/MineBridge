"""Small Qt worker helpers for background tasks."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, Qt, QThread, Signal, Slot


class FunctionWorker(QObject):
    """Run a Python callable in a QThread."""

    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, function: Callable[[], Any]) -> None:
        super().__init__()
        self.function = function

    def run(self) -> None:
        try:
            self.finished.emit(self.function())
        except Exception as exc:  # noqa: BLE001 - UI needs a friendly message for any task error.
            self.failed.emit(str(exc))


class CallbackDispatcher(QObject):
    """Deliver worker results back to the GUI thread."""

    def __init__(
        self,
        on_finished: Callable[[Any], None],
        on_failed: Callable[[str], None],
    ) -> None:
        super().__init__()
        self.on_finished = on_finished
        self.on_failed = on_failed

    @Slot(object)
    def handle_finished(self, result: object) -> None:
        self.on_finished(result)
        self.deleteLater()

    @Slot(str)
    def handle_failed(self, message: str) -> None:
        self.on_failed(message)
        self.deleteLater()


class GuiStringBridge(QObject):
    """Bridge a service string callback back into the Qt GUI thread."""

    value = Signal(str)

    def __init__(self, receiver: Callable[[str], None]) -> None:
        super().__init__()
        self.value.connect(receiver, Qt.ConnectionType.QueuedConnection)

    def emit(self, value: str) -> None:
        self.value.emit(value)


def run_in_thread(
    function: Callable[[], Any],
    on_finished: Callable[[Any], None],
    on_failed: Callable[[str], None],
) -> QThread:
    """Start a callable in a QThread and return the running thread."""
    thread = QThread()
    worker = FunctionWorker(function)
    dispatcher = CallbackDispatcher(on_finished, on_failed)
    thread._minebridge_worker = worker  # type: ignore[attr-defined]
    thread._minebridge_dispatcher = dispatcher  # type: ignore[attr-defined]
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    worker.finished.connect(
        dispatcher.handle_finished,
        Qt.ConnectionType.QueuedConnection,
    )
    worker.failed.connect(
        dispatcher.handle_failed,
        Qt.ConnectionType.QueuedConnection,
    )
    worker.finished.connect(thread.quit)
    worker.failed.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    worker.failed.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)

    def clear_worker_reference() -> None:
        thread._minebridge_worker = None  # type: ignore[attr-defined]

    thread._minebridge_cleanup = clear_worker_reference  # type: ignore[attr-defined]
    thread.finished.connect(clear_worker_reference)
    thread.start()
    return thread
