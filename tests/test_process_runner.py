from __future__ import annotations

import sys
import threading

from minebridge_frp.app.services.process_runner import ProcessRunner


def test_process_runner_streams_output_and_finishes():
    runner = ProcessRunner()
    lines: list[str] = []
    codes: list[int] = []
    finished = threading.Event()
    runner.output.connect(lines.append)
    runner.finished.connect(lambda code: (codes.append(code), finished.set()))

    runner.start(
        sys.executable,
        ["-u", "-c", "print('minebridge-ready')"],
    )

    assert finished.wait(5)
    assert lines == ["minebridge-ready"]
    assert codes == [0]
    assert not runner.is_running


def test_process_runner_sends_stdin():
    runner = ProcessRunner()
    lines: list[str] = []
    finished = threading.Event()
    runner.output.connect(lines.append)
    runner.started.connect(lambda: runner.send_line("stop"))
    runner.finished.connect(lambda _code: finished.set())

    runner.start(
        sys.executable,
        ["-u", "-c", "import sys; print(sys.stdin.readline().strip())"],
    )

    assert finished.wait(5)
    assert lines == ["stop"]
