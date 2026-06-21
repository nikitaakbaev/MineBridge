from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from minebridge_frp.app.core.exceptions import ConfigurationError
from minebridge_frp.app.models.minecraft import MinecraftConfig
from minebridge_frp.app.services.minecraft_manager import (
    MinecraftManager,
    format_server_properties,
    parse_server_properties,
)


def test_parse_server_properties_ignores_comments():
    text = """
    # comment
    server-port=25565
    online-mode=true
    motd=MineBridge FRP server
    """

    assert parse_server_properties(text) == {
        "server-port": "25565",
        "online-mode": "true",
        "motd": "MineBridge FRP server",
    }


def test_format_server_properties_formats_booleans_lowercase():
    text = format_server_properties({"online-mode": True, "server-port": 25565})

    assert "online-mode=true" in text
    assert "server-port=25565" in text


def test_server_properties_round_trip_preserves_values():
    values = {
        "server-port": 25565,
        "online-mode": False,
        "difficulty": "hard",
        "max-players": 12,
        "motd": "Friends only",
    }

    reparsed = parse_server_properties(format_server_properties(values))

    assert reparsed == {
        "server-port": "25565",
        "online-mode": "false",
        "difficulty": "hard",
        "max-players": "12",
        "motd": "Friends only",
    }


def test_parse_server_properties_keeps_values_with_equals():
    text = "motd=MineBridge=FRP\nserver-port=25565\n"

    assert parse_server_properties(text)["motd"] == "MineBridge=FRP"


def _config(jar: Path) -> MinecraftConfig:
    return MinecraftConfig(
        server_dir=str(jar.parent),
        jar_path=str(jar),
        java_path="/fake/java",
        xms="1G",
        xmx="2G",
    )


def _prepare_server_dir(tmp_path: Path, *, eula: bool = True) -> Path:
    if eula:
        (tmp_path / "eula.txt").write_text("eula=true\n", encoding="utf-8")
    return tmp_path


def test_start_server_uses_java_for_jar(tmp_path: Path):
    _prepare_server_dir(tmp_path)
    jar = tmp_path / "server.jar"
    jar.write_bytes(b"")

    manager = MinecraftManager()
    captured: dict[str, object] = {}

    def fake_start_command(command, working_directory=None, env=None):
        captured["command"] = list(command)
        captured["env"] = env

    with patch.object(manager.process, "start_command", side_effect=fake_start_command):
        manager.start_server(_config(jar))

    command = captured["command"]
    assert command[0] == "/fake/java"
    assert "-Xms1G" in command
    assert "-Xmx2G" in command
    assert "-jar" in command
    assert command[-1] == "nogui"
    assert captured["env"] is None


def test_start_server_runs_shell_script(tmp_path: Path):
    _prepare_server_dir(tmp_path)
    script = tmp_path / "run.sh"
    script.write_text("#!/usr/bin/env bash\n", encoding="utf-8")

    manager = MinecraftManager()
    captured: dict[str, object] = {}

    def fake_start_command(command, working_directory=None, env=None):
        captured["command"] = list(command)
        captured["env"] = env

    with patch.object(manager.process, "start_command", side_effect=fake_start_command), patch(
        "minebridge_frp.app.services.minecraft_manager.shutil.which",
        return_value="/usr/bin/bash",
    ):
        manager.start_server(_config(script))

    assert captured["command"] == ["/usr/bin/bash", str(script), "nogui"]
    assert captured["env"] == {"JAVA_TOOL_OPTIONS": "-Xms1G -Xmx2G"}


def test_start_server_rejects_bat_outside_windows(tmp_path: Path):
    script = tmp_path / "run.bat"

    manager = MinecraftManager()
    with patch("minebridge_frp.app.services.minecraft_manager.os.name", "posix"):
        with pytest.raises(ConfigurationError, match=r"\.bat/\.cmd"):
            manager._build_batch_script_command(script)


@pytest.mark.skipif(os.name != "nt", reason="cmd.exe only on Windows")
def test_start_server_runs_bat_on_windows(tmp_path: Path):
    _prepare_server_dir(tmp_path)
    script = tmp_path / "run.bat"
    script.write_text("@echo off\n", encoding="utf-8")

    manager = MinecraftManager()
    captured: dict[str, object] = {}

    def fake_start_command(command, working_directory=None, env=None):
        captured["command"] = list(command)
        captured["env"] = env

    with patch.object(manager.process, "start_command", side_effect=fake_start_command):
        manager.start_server(_config(script))

    command = captured["command"]
    assert command[1] == "/c"
    assert command[2] == str(script)
    assert command[3] == "nogui"
    assert captured["env"] == {"JAVA_TOOL_OPTIONS": "-Xms1G -Xmx2G"}


def test_start_server_requires_eula(tmp_path: Path):
    jar = tmp_path / "server.jar"
    jar.write_bytes(b"")

    manager = MinecraftManager()
    with pytest.raises(ConfigurationError, match="EULA"):
        manager.start_server(_config(jar))
