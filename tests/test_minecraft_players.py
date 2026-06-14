from __future__ import annotations

from minebridge_frp.app.services.minecraft_manager import MinecraftManager


def _join_line(name: str) -> str:
    return f"[15:46:16] [Server thread/INFO]: {name} joined the game"


def _left_line(name: str) -> str:
    return f"[15:46:16] [Server thread/INFO]: {name} left the game"


def test_minecraft_manager_tracks_player_join_and_leave():
    manager = MinecraftManager()
    events: list[tuple[int, list[str]]] = []
    manager.players_changed.connect(lambda count, players: events.append((count, list(players))))

    manager._handle_output(_join_line("Steve"))
    manager._handle_output(_join_line("Alex"))
    manager._handle_output(_left_line("Steve"))

    assert manager.player_count == 1
    assert manager.players == ["Alex"]
    assert events[-1] == (1, ["Alex"])


def test_minecraft_manager_ignores_duplicate_joins():
    manager = MinecraftManager()

    manager._handle_output(_join_line("Steve"))
    manager._handle_output(_join_line("Steve"))

    assert manager.player_count == 1


def test_minecraft_manager_emits_ready_on_done_line():
    manager = MinecraftManager()
    ready: list[bool] = []
    manager.ready.connect(lambda: ready.append(True))

    manager._handle_output(
        '[15:46:16] [Server thread/INFO]: Done (12.345s)! For help, type "help"'
    )

    assert ready == [True]


def test_minecraft_manager_pid_is_none_when_not_running():
    assert MinecraftManager().pid is None
