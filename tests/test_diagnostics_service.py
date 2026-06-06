from __future__ import annotations

from minebridge_frp.app.core.app_context import AppContext
from minebridge_frp.app.models.profile import ProfileBundle
from minebridge_frp.app.services.diagnostics_service import DiagnosticsService


def test_diagnostics_reports_missing_profile_requirements(tmp_path, monkeypatch):
    monkeypatch.setenv("MINEBRIDGE_HOME", str(tmp_path))
    context = AppContext.create()
    service = DiagnosticsService(context)
    bundle = ProfileBundle.model_validate(
        {
            "profile": {"name": "test"},
            "vps": {},
            "minecraft": {},
            "tunnel": {},
        }
    )

    results = service.run_profile_checks(bundle)
    names_by_status = {(result.name, result.status) for result in results}

    assert ("Server folder", "ERROR") in names_by_status
    assert ("server.jar", "ERROR") in names_by_status
    assert ("FRP token", "ERROR") in names_by_status
    assert ("VPS host", "ERROR") in names_by_status
