"""Small Qt worker helpers for background tasks."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, QThread, Signal


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


def run_in_thread(
    function: Callable[[], Any],
    on_finished: Callable[[Any], None],
    on_failed: Callable[[str], None],
) -> QThread:
    """Start a callable in a QThread and return the running thread."""
    thread = QThread()
    worker = FunctionWorker(function)
    thread._minebridge_worker = worker  # type: ignore[attr-defined]
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    worker.finished.connect(on_finished)
    worker.failed.connect(on_failed)
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
