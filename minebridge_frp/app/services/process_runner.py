"""UI-neutral process runner used by backend services."""

from __future__ import annotations

import subprocess
import threading
from collections.abc import Sequence
from pathlib import Path

from minebridge_frp.app.core.exceptions import ServiceError
from minebridge_frp.app.services.events import CallbackSignal


class ProcessRunner:
    """Manage a long-running subprocess and stream output through callbacks."""

    def __init__(self) -> None:
        self.process: subprocess.Popen[str] | None = None
        self.output = CallbackSignal[[str]]()
        self.started = CallbackSignal[[]]()
        self.finished = CallbackSignal[[int]]()
        self.error = CallbackSignal[[str]]()
        self._reader_thread: threading.Thread | None = None
        self._waiter_thread: threading.Thread | None = None
        self._lock = threading.RLock()

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self.process is not None and self.process.poll() is None

    def start(
        self,
        program: str | Path,
        arguments: Sequence[str],
        working_directory: str | Path | None = None,
    ) -> None:
        with self._lock:
            if self.is_running:
                raise ServiceError("Процесс уже запущен.")

            try:
                self.process = subprocess.Popen(
                    [str(program), *arguments],
                    cwd=str(working_directory) if working_directory is not None else None,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    bufsize=1,
                )
            except OSError as exc:
                self.process = None
                raise ServiceError(f"Не удалось запустить процесс: {exc}") from exc

            self._reader_thread = threading.Thread(
                target=self._read_output,
                name="minebridge-process-output",
                daemon=True,
            )
            self._waiter_thread = threading.Thread(
                target=self._wait_for_exit,
                name="minebridge-process-wait",
                daemon=True,
            )
            self._reader_thread.start()
            self._waiter_thread.start()

        self.started.emit()

    def send_line(self, line: str) -> None:
        with self._lock:
            process = self.process
            if process is None or process.poll() is not None or process.stdin is None:
                raise ServiceError("Процесс не запущен.")
            try:
                process.stdin.write(f"{line.rstrip()}\n")
                process.stdin.flush()
            except OSError as exc:
                raise ServiceError(f"Не удалось отправить команду процессу: {exc}") from exc

    def terminate(self, timeout_seconds: float = 3.0) -> None:
        with self._lock:
            process = self.process
        if process is None or process.poll() is not None:
            return

        process.terminate()
        try:
            process.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            process.kill()

    def kill(self) -> None:
        with self._lock:
            process = self.process
        if process is not None and process.poll() is None:
            process.kill()

    def _read_output(self) -> None:
        with self._lock:
            process = self.process
        if process is None or process.stdout is None:
            return

        try:
            for line in process.stdout:
                self.output.emit(line.rstrip("\r\n"))
        except OSError as exc:
            self.error.emit(str(exc))

    def _wait_for_exit(self) -> None:
        with self._lock:
            process = self.process
        if process is None:
            return
        code = process.wait()
        self.finished.emit(code)
