"""Live system and Minecraft-process metrics sampler.

The sampler runs in a background thread and emits a metrics snapshot at a fixed
interval through a :class:`CallbackSignal`. The Electron/React frontend renders
these snapshots as live charts (CPU, RAM, network, and players online).
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable

import psutil

from minebridge_frp.app.services.events import CallbackSignal

_MB = 1024 * 1024


class MetricsSampler:
    """Periodically sample host and Minecraft-process resource usage."""

    def __init__(
        self,
        pid_provider: Callable[[], int | None],
        players_provider: Callable[[], int] | None = None,
        running_provider: Callable[[], bool] | None = None,
        interval_seconds: float = 2.0,
    ) -> None:
        self.sample = CallbackSignal[[dict]]()
        self._pid_provider = pid_provider
        self._players_provider = players_provider or (lambda: 0)
        self._running_provider = running_provider or (lambda: False)
        self._interval = max(0.5, interval_seconds)
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._cpu_count = psutil.cpu_count(logical=True) or 1

        self._proc: psutil.Process | None = None
        self._proc_pid: int | None = None
        self._last_net: tuple[float, int, int] | None = None
        self._last_snapshot: dict | None = None

    @property
    def last_snapshot(self) -> dict | None:
        return self._last_snapshot

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        # Prime the system-wide CPU counter so the first reading is meaningful.
        psutil.cpu_percent(interval=None)
        self._thread = threading.Thread(
            target=self._run,
            name="minebridge-metrics-sampler",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=self._interval + 1.0)
        self._thread = None

    def _run(self) -> None:
        while not self._stop_event.wait(self._interval):
            try:
                snapshot = self._collect()
            except Exception:  # noqa: BLE001 - metrics must never crash the app
                continue
            self._last_snapshot = snapshot
            self.sample.emit(snapshot)

    def _resolve_process(self) -> psutil.Process | None:
        pid = self._pid_provider()
        if pid is None:
            self._proc = None
            self._proc_pid = None
            return None
        if self._proc is None or self._proc_pid != pid:
            try:
                self._proc = psutil.Process(pid)
                self._proc_pid = pid
                # Prime per-process CPU counter.
                self._proc.cpu_percent(interval=None)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                self._proc = None
                self._proc_pid = None
        return self._proc

    def _collect(self) -> dict:
        now = time.time()
        cpu = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        ram_used_mb = round((memory.total - memory.available) / _MB)
        ram_total_mb = round(memory.total / _MB)

        net = psutil.net_io_counters()
        net_up_kbps = 0.0
        net_down_kbps = 0.0
        if self._last_net is not None:
            prev_t, prev_sent, prev_recv = self._last_net
            elapsed = max(now - prev_t, 1e-6)
            net_up_kbps = round(max(net.bytes_sent - prev_sent, 0) / 1024 / elapsed, 1)
            net_down_kbps = round(max(net.bytes_recv - prev_recv, 0) / 1024 / elapsed, 1)
        self._last_net = (now, net.bytes_sent, net.bytes_recv)

        server_cpu = 0.0
        server_ram_mb = 0.0
        process = self._resolve_process()
        if process is not None:
            try:
                raw_cpu = process.cpu_percent(interval=None)
                server_cpu = round(raw_cpu / self._cpu_count, 1)
                server_ram_mb = round(process.memory_info().rss / _MB, 1)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                server_cpu = 0.0
                server_ram_mb = 0.0

        return {
            "ts": int(now * 1000),
            "time": time.strftime("%H:%M:%S", time.localtime(now)),
            "cpu": round(cpu, 1),
            "ram_percent": round(memory.percent, 1),
            "ram_used_mb": ram_used_mb,
            "ram_total_mb": ram_total_mb,
            "net_up_kbps": net_up_kbps,
            "net_down_kbps": net_down_kbps,
            "server_running": bool(self._running_provider()),
            "server_cpu": server_cpu,
            "server_ram_mb": server_ram_mb,
            "players": int(self._players_provider()),
        }
