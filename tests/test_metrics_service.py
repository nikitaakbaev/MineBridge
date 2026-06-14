from __future__ import annotations

import os

from minebridge_frp.app.services.metrics_service import MetricsSampler


def test_metrics_sampler_collects_system_snapshot():
    sampler = MetricsSampler(pid_provider=lambda: None, interval_seconds=0.5)
    snapshot = sampler._collect()

    for key in ("ts", "cpu", "ram_percent", "ram_used_mb", "ram_total_mb", "players"):
        assert key in snapshot
    assert snapshot["ram_total_mb"] > 0
    assert snapshot["server_running"] is False
    assert snapshot["players"] == 0


def test_metrics_sampler_reports_process_for_current_pid():
    sampler = MetricsSampler(
        pid_provider=lambda: os.getpid(),
        players_provider=lambda: 3,
        running_provider=lambda: True,
        interval_seconds=0.5,
    )
    # First sample primes the per-process CPU counter.
    sampler._collect()
    snapshot = sampler._collect()

    assert snapshot["server_running"] is True
    assert snapshot["server_ram_mb"] > 0
    assert snapshot["players"] == 3
