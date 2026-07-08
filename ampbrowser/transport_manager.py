from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import os
import shutil
import socket
import subprocess
import time
from urllib.parse import urlparse

from .adapters import TransportStatus, adapter_for
from .config import AppConfig


ARTI_RELATIVE_PATH = Path("providers/arti/bin/arti")


@dataclass(frozen=True)
class TorProvider:
    kind: str
    binary: str


@dataclass(frozen=True)
class ManagedTransportResult:
    transport: str
    provider: str
    status: str
    endpoint: str
    owned: bool
    pid: int
    state_dir: str
    command: tuple[str, ...]
    message: str

    @property
    def ready(self) -> bool:
        return self.status in {"ready", "started"}


def ensure_transport_ready(
    transport: str,
    *,
    config: AppConfig,
    root: Path,
    status: TransportStatus | None = None,
    wait_seconds: float = 20.0,
) -> ManagedTransportResult:
    adapter = adapter_for(transport)
    if adapter is None:
        return ManagedTransportResult(transport, "-", "unsupported", "-", False, 0, "-", (), "transport adapter not found")

    status = status or adapter.inspect()
    if status.adoptable:
        return ManagedTransportResult(
            transport,
            "-",
            "ready",
            status.endpoint,
            False,
            0,
            _managed_state_dir(root, config, transport),
            (),
            f"adopted existing {transport} transport",
        )

    if transport != "tor":
        return ManagedTransportResult(
            transport,
            "-",
            "unsupported",
            status.endpoint,
            False,
            0,
            _managed_state_dir(root, config, transport),
            (),
            f"managed start for {transport} is not implemented yet",
        )

    return _start_tor(config=config, root=root, endpoint=status.endpoint, wait_seconds=wait_seconds)


def _start_tor(
    *,
    config: AppConfig,
    root: Path,
    endpoint: str,
    wait_seconds: float,
) -> ManagedTransportResult:
    provider = _tor_provider(config)
    state_dir = _managed_state_dir(root, config, "tor")
    if not provider:
        return ManagedTransportResult(
            "tor",
            "-",
            "missing-provider",
            endpoint,
            False,
            0,
            state_dir,
            (),
            "Tor provider not found; run tools/browser-tor-provider-build.sh or set AMPB_ARTI_BIN, AMPB_TOR_BIN, or transports.tor.binary_path",
        )

    state_path = Path(state_dir)
    state_path.mkdir(parents=True, exist_ok=True)
    _chmod_private(state_path)

    command = _tor_command(provider, endpoint=endpoint, state_path=state_path)
    try:
        with (state_path / f"{provider.kind}.log").open("ab") as log_file:
            process = subprocess.Popen(command, stdout=log_file, stderr=log_file, start_new_session=True)  # noqa: S603
    except OSError as exc:
        return ManagedTransportResult(
            "tor",
            provider.kind,
            "start-failed",
            endpoint,
            False,
            0,
            state_dir,
            command,
            f"managed {provider.kind} could not start: {exc}",
        )

    if _wait_for_endpoint(endpoint, timeout_seconds=wait_seconds):
        return ManagedTransportResult(
            "tor",
            provider.kind,
            "started",
            endpoint,
            True,
            process.pid,
            state_dir,
            command,
            f"started managed {provider.kind} transport",
        )

    process.terminate()
    return ManagedTransportResult(
        "tor",
        provider.kind,
        "start-timeout",
        endpoint,
        True,
        process.pid,
        state_dir,
        command,
        f"managed {provider.kind} did not become ready at {endpoint}",
    )


def _tor_provider(config: AppConfig) -> TorProvider | None:
    arti_path = os.environ.get("AMPB_ARTI_BIN") or _bundled_arti_path()
    if arti_path:
        return TorProvider("arti", arti_path)

    tor_path = os.environ.get("AMPB_TOR_BIN")
    if tor_path:
        return TorProvider("tor", tor_path)

    config_path = config.transport_binary("tor")
    if config_path:
        return TorProvider(_infer_provider_kind(config_path), config_path)

    system_tor = shutil.which("tor")
    if system_tor:
        return TorProvider("tor", system_tor)
    return None


def _bundled_arti_path() -> str:
    build_root = Path(os.environ.get("AMPB_BROWSER_BUILD_ROOT", "/tmp/ampb-browser-build"))
    candidate = build_root / ARTI_RELATIVE_PATH
    if candidate.exists() and candidate.is_file():
        return str(candidate)
    return ""


def _infer_provider_kind(binary_path: str) -> str:
    name = Path(binary_path).name.lower()
    if name.startswith("arti"):
        return "arti"
    return "tor"


def _tor_command(provider: TorProvider, *, endpoint: str, state_path: Path) -> tuple[str, ...]:
    host, port = _endpoint_host_port(endpoint)
    if provider.kind == "arti":
        state_dir = state_path / "arti-state"
        cache_dir = state_path / "arti-cache"
        state_dir.mkdir(parents=True, exist_ok=True)
        cache_dir.mkdir(parents=True, exist_ok=True)
        _chmod_private(state_dir)
        _chmod_private(cache_dir)
        return (
            provider.binary,
            "proxy",
            "-p",
            str(port),
            "-o",
            f"storage.state_dir={json.dumps(str(state_dir))}",
            "-o",
            f"storage.cache_dir={json.dumps(str(cache_dir))}",
            "-l",
            "warn",
        )

    data_dir = state_path / "tor-data"
    data_dir.mkdir(parents=True, exist_ok=True)
    _chmod_private(data_dir)
    return (
        provider.binary,
        "--SocksPort",
        f"{host}:{port}",
        "--DataDirectory",
        str(data_dir),
        "--ClientOnly",
        "1",
        "--Log",
        f"notice file {state_path / 'tor.log'}",
    )


def _managed_state_dir(root: Path, config: AppConfig, transport: str) -> str:
    return str(root / config.state_dir / "transports" / transport)


def _chmod_private(path: Path) -> None:
    try:
        path.chmod(0o700)
    except OSError:
        pass


def _wait_for_endpoint(endpoint: str, *, timeout_seconds: float) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() <= deadline:
        host, port = _endpoint_host_port(endpoint)
        if _can_connect(host, port):
            return True
        time.sleep(0.2)
    return False


def _can_connect(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.2):
            return True
    except OSError:
        return False


def _endpoint_host_port(endpoint: str) -> tuple[str, int]:
    parsed = urlparse(endpoint)
    return parsed.hostname or "127.0.0.1", parsed.port or 9050
