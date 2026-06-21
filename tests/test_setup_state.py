from __future__ import annotations

import json
from pathlib import Path

import pytest

from minebridge_frp.app.core.app_context import AppContext
from minebridge_frp.app.models.setup import SetupState
from minebridge_frp.app.services.setup_state import SetupStateService


@pytest.fixture
def context(tmp_path: Path) -> AppContext:
    return AppContext(
        config_dir=tmp_path / "config",
        data_dir=tmp_path / "data",
        log_dir=tmp_path / "log",
        database_path=tmp_path / "data" / "db.sqlite3",
    )


def test_load_returns_default_when_missing(context: AppContext):
    service = SetupStateService(context)

    state = service.load()

    assert state == SetupState(completed=False, current_step="vps")


def test_save_then_load_round_trips(context: AppContext):
    service = SetupStateService(context)

    saved = service.save(SetupState(completed=True, current_step="done"))
    reloaded = service.load()

    assert saved == reloaded
    assert reloaded.completed is True
    assert reloaded.current_step == "done"


def test_update_partial_keeps_existing_fields(context: AppContext):
    service = SetupStateService(context)
    service.save(SetupState(completed=False, current_step="vps"))

    updated = service.update(current_step="tunnel")

    assert updated.completed is False
    assert updated.current_step == "tunnel"


def test_load_recovers_from_corrupted_file(context: AppContext):
    service = SetupStateService(context)
    context.config_dir.mkdir(parents=True, exist_ok=True)
    (context.config_dir / "setup.json").write_text("not json", encoding="utf-8")

    state = service.load()

    assert state == SetupState()


def test_save_writes_pretty_json(context: AppContext):
    service = SetupStateService(context)
    service.save(SetupState(completed=True, current_step="server"))

    payload = json.loads((context.config_dir / "setup.json").read_text(encoding="utf-8"))

    assert payload == {"completed": True, "current_step": "server"}
