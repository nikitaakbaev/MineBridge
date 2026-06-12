"""Small callback event helpers for UI-neutral services."""

from __future__ import annotations

from collections.abc import Callable
from threading import RLock
from typing import Generic, ParamSpec

P = ParamSpec("P")


class CallbackSignal(Generic[P]):
    """Minimal signal-like callback registry without a GUI framework dependency."""

    def __init__(self) -> None:
        self._callbacks: list[Callable[P, None]] = []
        self._lock = RLock()

    def connect(self, callback: Callable[P, None]) -> None:
        with self._lock:
            if callback not in self._callbacks:
                self._callbacks.append(callback)

    def disconnect(self, callback: Callable[P, None]) -> None:
        with self._lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)

    def emit(self, *args: P.args, **kwargs: P.kwargs) -> None:
        with self._lock:
            callbacks = tuple(self._callbacks)
        for callback in callbacks:
            callback(*args, **kwargs)
