from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import shutil
import socket
import subprocess
import time
from urllib.parse import urlparse

from .adapters import TransportStatus, adapter_for
from .config import AppConfig


@dataclass(frozen=True)
class ManagedTransportResult:
    transport: str
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
        return ManagedTransportResult(transport, "unsupported", "-", False, 0, "-", (), "transport adapter not found")

    status = status or adapter.inspect()
    if status.adoptable:
        return ManagedTransportResult(
            transport,
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
    binary = _transport_binary(config, "tor")
    state_dir = _managed_state_dir(root, config, "tor")
    if not binary:
        return ManagedTransportResult(
            "tor",
            "missing-provider",
            endpoint,
            False,
            0,
            state_dir,
            (),
            "Tor provider not found; set AMPB_TOR_BIN or transports.tor.binary_path",
        )

    state_path = Path(state_dir)
    data_dir = state_path / "data"
    log_path = state_path / "tor.log"
    data_dir.mkdir(parents=True, exist_ok=True)

    host, port = _endpoint_host_port(endpoint)
    command = (
        binary,
        "--SocksPort",
        f"{host}:{port}",
        "--DataDirectory",
        str(data_dir),
        "--ClientOnly",
        "1",
        "--Log",
        f"notice file {log_path}",
    )
    try:
        process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # noqa: S603
    except OSError as exc:
        return ManagedTransportResult(
            "tor",
            "start-failed",
            endpoint,
            False,
            0,
            state_dir,
            command,
            f"managed Tor could not start: {exc}",
        )

    if _wait_for_endpoint(endpoint, timeout_seconds=wait_seconds):
        return ManagedTransportResult(
            "tor",
            "started",
            endpoint,
            True,
            process.pid,
            state_dir,
            command,
            "started managed Tor transport",
        )

    process.terminate()
    return ManagedTransportResult(
        "tor",
        "start-timeout",
        endpoint,
        True,
        process.pid,
        state_dir,
        command,
        f"managed Tor did not become ready at {endpoint}",
    )


def _transport_binary(config: AppConfig, transport: str) -> str:
    env_name = f"AMPB_{transport.upper()}_BIN"
    env_path = os.environ.get(env_name)
    if env_path:
        return env_path
    config_path = config.transport_binary(transport)
    if config_path:
        return config_path
    if transport == "tor":
        return shutil.which("tor") or ""
    return ""


def _managed_state_dir(root: Path, config: AppConfig, transport: str) -> str:
    return str(root / config.state_dir / "transports" / transport)


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
