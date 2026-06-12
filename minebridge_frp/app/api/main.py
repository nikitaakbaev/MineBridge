"""Backend API entry point for Electron."""

from __future__ import annotations

import logging

import uvicorn

from minebridge_frp.app.api.app import create_app
from minebridge_frp.app.core.app_context import AppContext
from minebridge_frp.app.core.logger import setup_logging


def main() -> int:
    context = AppContext.create()
    setup_logging(context.log_dir)
    logging.getLogger(__name__).info("Starting MineBridge FRP API")
    uvicorn.run(create_app(context), host="127.0.0.1", port=47831, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
