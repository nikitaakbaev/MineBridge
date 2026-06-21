from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from minebridge_frp.app.services.detection import (
    detect_java_installations,
    detect_server_launchers,
)


def test_detect_launchers_prefers_run_sh_over_jar(tmp_path: Path):
    (tmp_path / "server.jar").write_bytes(b"")
    (tmp_path / "run.sh").write_text("#!/bin/bash\n", encoding="utf-8")
    (tmp_path / "log4j-core.jar").write_bytes(b"")

    candidates = detect_server_launchers(tmp_path)

    assert candidates[0].path.endswith("run.sh")
    assert candidates[0].kind == "shell"
    assert candidates[0].score > candidates[1].score


def test_detect_launchers_finds_paper_jar(tmp_path: Path):
    (tmp_path / "paper-1.21.4.jar").write_bytes(b"")
    (tmp_path / "log4j-core.jar").write_bytes(b"")

    candidates = detect_server_launchers(tmp_path)

    assert candidates[0].path.endswith("paper-1.21.4.jar")
    assert candidates[0].kind == "jar"


def test_detect_launchers_skips_user_jvm_args(tmp_path: Path):
    (tmp_path / "user_jvm_args.txt").write_text("-Xmx2G\n", encoding="utf-8")
    (tmp_path / "run.bat").write_text("@echo off\n", encoding="utf-8")

    candidates = detect_server_launchers(tmp_path)

    assert any(c.path.endswith("run.bat") for c in candidates)
    assert all(not c.path.endswith("user_jvm_args.txt") for c in candidates)


def test_detect_launchers_returns_empty_for_missing_dir(tmp_path: Path):
    assert detect_server_launchers(tmp_path / "missing") == []


def test_detect_java_installations_deduplicates_and_sorts(tmp_path: Path):
    java17 = tmp_path / "java17" / "bin"
    java21 = tmp_path / "java21" / "bin"
    java17.mkdir(parents=True)
    java21.mkdir(parents=True)
    j17 = java17 / "java"
    j21 = java21 / "java"
    j17.write_text("", encoding="utf-8")
    j21.write_text("", encoding="utf-8")

    candidates = iter([j17, j17, j21])

    def fake_version(path: Path) -> str:
        return "21.0.2" if "21" in str(path) else "17.0.10"

    with patch(
        "minebridge_frp.app.services.detection._candidate_java_paths",
        return_value=candidates,
    ), patch(
        "minebridge_frp.app.services.detection._java_version",
        side_effect=fake_version,
    ), patch(
        "minebridge_frp.app.services.detection.shutil.which",
        return_value=None,
    ):
        result = detect_java_installations()

    versions = [item.version for item in result]
    assert versions == ["21.0.2", "17.0.10"]

