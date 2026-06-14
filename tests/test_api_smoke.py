from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from minebridge_frp.app.api.app import create_app  # noqa: E402
from minebridge_frp.app.core.app_context import AppContext  # noqa: E402


def test_api_health_and_profiles(tmp_path):
    data_dir = tmp_path / "data"
    context = AppContext(
        config_dir=tmp_path / "config",
        data_dir=data_dir,
        log_dir=tmp_path / "logs",
        database_path=data_dir / "minebridge-frp.sqlite3",
    )
    client = TestClient(create_app(context))

    assert client.get("/api/health").json() == {"message": "ok"}

    profiles = client.get("/api/profiles/vps").json()
    assert profiles
    assert profiles[0]["name"] == "Профиль по умолчанию"


def test_api_runtime_state_and_metrics(tmp_path):
    data_dir = tmp_path / "data"
    context = AppContext(
        config_dir=tmp_path / "config",
        data_dir=data_dir,
        log_dir=tmp_path / "logs",
        database_path=data_dir / "minebridge-frp.sqlite3",
    )
    client = TestClient(create_app(context))

    state = client.get("/api/runtime/state").json()
    assert state["minecraft_status"] == "idle"
    assert state["frpc_status"] == "idle"
    assert state["player_count"] == 0

    # No sample yet because the background sampler only runs under lifespan.
    assert client.get("/api/metrics/snapshot").status_code == 200


def test_api_health_includes_cors_header(tmp_path):
    data_dir = tmp_path / "data"
    context = AppContext(
        config_dir=tmp_path / "config",
        data_dir=data_dir,
        log_dir=tmp_path / "logs",
        database_path=data_dir / "minebridge-frp.sqlite3",
    )
    client = TestClient(create_app(context))

    response = client.get("/api/health", headers={"Origin": "http://127.0.0.1:5173"})
    assert response.headers.get("access-control-allow-origin") == "*"
