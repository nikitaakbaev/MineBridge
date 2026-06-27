"""Download official FRP binaries needed by the app bundle.

The resulting binaries are placed under resources/frp-bundled/<platform>/.
This lets the installer ship with frpc/frps already present instead of
downloading them on first launch.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path


FRP_RELEASES_API = "https://api.github.com/repos/fatedier/frp/releases/tags/{version}"
DEFAULT_VERSION = "v0.69.1"


@dataclass(frozen=True)
class PlatformTarget:
    os_name: str
    arch: str
    asset_suffix: str
    archive_suffix: str


TARGETS: dict[str, PlatformTarget] = {
    "windows": PlatformTarget("windows", "amd64", "windows_amd64", ".zip"),
    "linux": PlatformTarget("linux", "amd64", "linux_amd64", ".tar.gz"),
    "darwin": PlatformTarget("darwin", "amd64", "darwin_amd64", ".tar.gz"),
}


@dataclass(frozen=True)
class BundleRequest:
    target: PlatformTarget
    binary_name: str


def fetch_release(version: str) -> dict:
    url = FRP_RELEASES_API.format(version=version)
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def select_asset(release: dict, target: PlatformTarget) -> dict:
    for asset in release.get("assets", []):
        name = str(asset.get("name", "")).lower()
        if target.asset_suffix in name and name.endswith(target.archive_suffix):
            return asset
    raise RuntimeError(f"Could not find FRP asset for {target.asset_suffix}")


def download_file(url: str, destination: Path) -> None:
    with urllib.request.urlopen(url, timeout=60) as response, destination.open("wb") as handle:
        shutil.copyfileobj(response, handle)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise RuntimeError(
            f"Could not read prepared binary {path}. "
            "It may have been quarantined or blocked by antivirus software."
        ) from exc
    return digest.hexdigest()


def extract_binary(
    archive_path: Path,
    target: PlatformTarget,
    binary_name: str,
    destination_dir: Path,
) -> Path:
    destination_dir.mkdir(parents=True, exist_ok=True)

    if archive_path.suffix == ".zip":
        with zipfile.ZipFile(archive_path) as archive:
            for member in archive.namelist():
                if member.endswith(f"/{binary_name}") or member == binary_name:
                    extracted = destination_dir / binary_name
                    with archive.open(member) as src, extracted.open("wb") as dst:
                        shutil.copyfileobj(src, dst)
                    return extracted
    else:
        with tarfile.open(archive_path) as archive:
            for member in archive.getmembers():
                if member.isfile() and Path(member.name).name == binary_name:
                    extracted = destination_dir / binary_name
                    with archive.extractfile(member) as src, extracted.open("wb") as dst:
                        if src is None:
                            break
                        shutil.copyfileobj(src, dst)
                    return extracted

    raise RuntimeError(f"Could not extract {binary_name} from {archive_path.name}")


def current_platform_target() -> PlatformTarget:
    target_key = sys.platform
    if target_key.startswith("win"):
        target_key = "windows"
    elif target_key.startswith("linux"):
        target_key = "linux"
    elif target_key.startswith("darwin"):
        target_key = "darwin"
    else:
        raise RuntimeError(f"Unsupported platform: {sys.platform}")

    return TARGETS[target_key]


def frpc_name(target: PlatformTarget) -> str:
    return "frpc.exe" if target.os_name == "windows" else "frpc"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default=DEFAULT_VERSION)
    parser.add_argument(
        "--output",
        default="resources/frp-bundled",
        help="Directory where platform subfolders will be created.",
    )
    args = parser.parse_args(argv)

    release = fetch_release(args.version)
    output_root = Path(args.output).resolve()
    current_target = current_platform_target()

    requests = [
        BundleRequest(current_target, frpc_name(current_target)),
        BundleRequest(TARGETS["linux"], "frps"),
    ]

    for request in requests:
        asset = select_asset(release, request.target)
        bundle_dir = output_root / request.target.asset_suffix

        with tempfile.TemporaryDirectory() as tmpdir:
            archive_path = Path(tmpdir) / asset["name"]
            download_file(asset["browser_download_url"], archive_path)
            extracted = extract_binary(
                archive_path,
                request.target,
                request.binary_name,
                bundle_dir,
            )

        if not extracted.exists():
            raise RuntimeError(
                f"Prepared binary disappeared before verification: {extracted}. "
                "It may have been quarantined or blocked by antivirus software."
            )
        digest = sha256_file(extracted)
        print(f"Prepared {extracted} ({digest}) from {asset['browser_download_url']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from None
