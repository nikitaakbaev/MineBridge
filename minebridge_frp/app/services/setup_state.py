"""Persist the first-run setup wizard state under the user's config directory."""

from __future__ import annotations

import json
import threading
from pathlib import Path

from minebridge_frp.app.core.app_context import AppContext
from minebridge_frp.app.models.setup import SetupState, SetupStep


class SetupStateService:
    """Read/write the setup wizard state as JSON in ``config_dir/setup.json``."""

    def __init__(self, context: AppContext) -> None:
        self._path: Path = context.config_dir / "setup.json"
        self._lock = threading.Lock()

    def load(self) -> SetupState:
        with self._lock:
            if not self._path.exists():
                return SetupState()
            try:
                payload = json.loads(self._path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return SetupState()
        try:
            return SetupState.model_validate(payload)
        except ValueError:
            return SetupState()

    def save(self, state: SetupState) -> SetupState:
        data = state.model_dump()
        payload = json.dumps(data, ensure_ascii=False, indent=2)
        with self._lock:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(payload, encoding="utf-8")
        return state

    def update(
        self,
        *,
        current_step: SetupStep | None = None,
        completed: bool | None = None,
    ) -> SetupState:
        current = self.load()
        next_state = current.model_copy(
            update={
                k: v
                for k, v in {"current_step": current_step, "completed": completed}.items()
                if v is not None
            }
        )
        return self.save(next_state)
