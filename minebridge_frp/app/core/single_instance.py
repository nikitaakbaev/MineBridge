"""Single-instance guard for the desktop application."""

from __future__ import annotations

import getpass
import re
import tempfile
from pathlib import Path

from PySide6.QtCore import QLockFile, QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket

DEFAULT_INSTANCE_KEY = "minebridge-frp"


class SingleInstanceGuard(QObject):
    """Prevent multiple GUI instances and notify the already running window."""

    message_received = Signal(str)

    def __init__(self, key: str = DEFAULT_INSTANCE_KEY) -> None:
        super().__init__()
        self.key = key
        self._server: QLocalServer | None = None
        self._lock = QLockFile(str(_lock_path_for_key(key)))
        self._lock.setStaleLockTime(0)

    def acquire(self) -> bool:
        if not self._lock.tryLock(0):
            self._notify_existing_instance()
            return False

        self._start_server()
        return True

    def _start_server(self) -> None:
        QLocalServer.removeServer(self.key)
        server = QLocalServer(self)
        server.newConnection.connect(self._handle_connection)
        if server.listen(self.key):
            self._server = server

    def _notify_existing_instance(self) -> bool:
        socket = QLocalSocket()
        socket.connectToServer(self.key)
        if not socket.waitForConnected(150):
            socket.abort()
            return False

        socket.write(b"raise")
        socket.flush()
        socket.waitForBytesWritten(150)
        socket.disconnectFromServer()
        return True

    def _handle_connection(self) -> None:
        if self._server is None:
            return

        while self._server.hasPendingConnections():
            socket = self._server.nextPendingConnection()
            socket.setParent(self)
            socket.readyRead.connect(lambda sock=socket: self._read_socket(sock))
            socket.disconnected.connect(socket.deleteLater)
            if socket.bytesAvailable():
                self._read_socket(socket)

    def _read_socket(self, socket: QLocalSocket) -> None:
        message = bytes(socket.readAll()).decode("utf-8", errors="replace").strip()
        if message:
            self.message_received.emit(message)


def _lock_path_for_key(key: str) -> Path:
    safe_key = re.sub(r"[^a-zA-Z0-9_.-]+", "-", key).strip("-") or "minebridge-frp"
    safe_user = re.sub(r"[^a-zA-Z0-9_.-]+", "-", getpass.getuser()).strip("-") or "user"
    return Path(tempfile.gettempdir()) / f"{safe_key}-{safe_user}.lock"
