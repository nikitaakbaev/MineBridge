"""Download service for FRP releases."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import requests

from minebridge_frp.app.core.exceptions import ServiceError
from minebridge_frp.app.utils.archive import extract_archive, make_executable
from minebridge_frp.app.utils.os_detect import PlatformInfo, detect_platform

FRP_RELEASES_API = "https://api.github.com/repos/fatedier/frp/releases"
DEFAULT_FRP_VERSION = "v0.69.1"


class DownloadService:
    """Download and unpack FRP release archives."""

    def __init__(self, storage_dir: Path) -> None:
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def download_frp(
        self,
        version: str | None = None,
        platform_info: PlatformInfo | None = None,
    ) -> Path:
        """Download FRP and return the directory containing extracted files."""
        platform_info = platform_info or detect_platform()
        release = self._fetch_release(version or DEFAULT_FRP_VERSION)
        asset = self._select_asset(release, platform_info)
        archive_path = self._download_asset(asset["browser_download_url"])

        extract_dir = self.storage_dir / release["tag_name"]
        extract_archive(archive_path, extract_dir)
        self._make_binaries_executable(extract_dir, platform_info)
        return extract_dir

    def _fetch_release(self, version: str) -> dict:
        url = f"{FRP_RELEASES_API}/tags/{version}"
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            raise ServiceError(f"Не удалось получить FRP release: HTTP {response.status_code}")
        return response.json()

    def _select_asset(self, release: dict, platform_info: PlatformInfo) -> dict:
        suffix = platform_info.frp_asset_suffix
        for asset in release.get("assets", []):
            name = asset.get("name", "").lower()
            if suffix in name and name.endswith((".tar.gz", ".zip")):
                return asset
        raise ServiceError(f"В релизе FRP не найден asset для {suffix}.")

    def _download_asset(self, url: str) -> Path:
        filename = Path(urlparse(url).path).name
        archive_path = self.storage_dir / filename

        with requests.get(url, stream=True, timeout=60) as response:
            if response.status_code != 200:
                raise ServiceError(f"Не удалось скачать FRP: HTTP {response.status_code}")
            with archive_path.open("wb") as file:
                for chunk in response.iter_content(chunk_size=1024 * 256):
                    if chunk:
                        file.write(chunk)

        return archive_path

    def _make_binaries_executable(self, extract_dir: Path, platform_info: PlatformInfo) -> None:
        for binary_name in (platform_info.frpc_binary_name, platform_info.frps_binary_name):
            for binary in extract_dir.rglob(binary_name):
                make_executable(binary)
