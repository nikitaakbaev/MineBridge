"""Operating system detection helpers."""

from __future__ import annotations

import platform
from dataclasses import dataclass


@dataclass(frozen=True)
class PlatformInfo:
    """Normalized platform information used by FRP downloads."""

    os_name: str
    arch: str

    @property
    def frp_asset_suffix(self) -> str:
        return f"{self.os_name}_{self.arch}"

    @property
    def frpc_binary_name(self) -> str:
        return "frpc.exe" if self.os_name == "windows" else "frpc"

    @property
    def frps_binary_name(self) -> str:
        return "frps.exe" if self.os_name == "windows" else "frps"


def detect_platform() -> PlatformInfo:
    """Detect current platform and normalize it for FRP release assets."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system.startswith("linux"):
        os_name = "linux"
    elif system.startswith("windows"):
        os_name = "windows"
    else:
        raise RuntimeError(f"Unsupported OS for FRP: {platform.system()}")

    if machine in {"x86_64", "amd64"}:
        arch = "amd64"
    else:
        raise RuntimeError(f"Unsupported architecture for FRP: {platform.machine()}")

    return PlatformInfo(os_name=os_name, arch=arch)
