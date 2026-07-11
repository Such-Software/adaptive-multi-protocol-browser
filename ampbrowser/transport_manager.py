from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import os
import signal
import shutil
import socket
import subprocess
import sys
import time
from urllib.parse import urlparse

from .adapters import TransportStatus, adapter_for
from .config import AppConfig


ARTI_RELATIVE_PATH = Path("providers/arti/bin/arti")
I2PD_RELATIVE_PATH = Path("providers/i2pd/bin/i2pd")
OWNED_STATE_FILE = "ampb-owned.json"


@dataclass(frozen=True)
class TorProvider:
    kind: str
    binary: str
    source: str


@dataclass(frozen=True)
class I2PProvider:
    kind: str
    binary: str
    source: str


@dataclass(frozen=True)
class SetupHint:
    message: str
    command: tuple[str, ...] = ()


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
    provider_source: str = "-"
    setup_hint: str = "-"
    install_command: tuple[str, ...] = ()

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

    owned = _owned_transport_result(transport, config=config, root=root, wait_seconds=wait_seconds)
    if owned:
        return owned

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
            provider_source="system-adopted",
        )

    if transport == "tor":
        return _start_tor(config=config, root=root, endpoint=status.endpoint, wait_seconds=wait_seconds)
    if transport == "i2p":
        return _start_i2p(config=config, root=root, endpoint=status.endpoint, wait_seconds=wait_seconds)

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


def transport_status(
    transport: str,
    *,
    config: AppConfig,
    root: Path,
) -> ManagedTransportResult:
    adapter = adapter_for(transport)
    if adapter is None:
        return ManagedTransportResult(transport, "-", "unsupported", "-", False, 0, "-", (), "transport adapter not found")

    owned = _owned_transport_result(transport, config=config, root=root, wait_seconds=0.1)
    if owned:
        return owned

    status = adapter.inspect()
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
            f"{transport} transport is running but not AMPB-owned",
            provider_source="system-adopted",
        )

    return ManagedTransportResult(
        transport,
        "-",
        "stopped",
        status.endpoint,
        False,
        0,
        _managed_state_dir(root, config, transport),
        (),
        f"{transport} transport is not running",
        setup_hint=_stopped_setup_hint(transport, config),
        install_command=_stopped_install_command(transport, config),
    )


def stop_managed_transport(
    transport: str,
    *,
    config: AppConfig,
    root: Path,
    wait_seconds: float = 5.0,
) -> ManagedTransportResult:
    state_path = _owned_state_path(root, config, transport)
    state = _read_owned_state(state_path)
    endpoint = str(state.get("endpoint") or _endpoint_for(transport))
    state_dir = _managed_state_dir(root, config, transport)
    provider = str(state.get("provider") or "-")
    provider_source = str(state.get("provider_source") or "-")
    command = tuple(str(part) for part in state.get("command", ()))
    pid = _state_pid(state)

    if not state or not pid:
        return ManagedTransportResult(
            transport,
            "-",
            "not-owned",
            endpoint,
            False,
            0,
            state_dir,
            (),
            f"no AMPB-owned {transport} process is recorded",
            provider_source=provider_source,
        )

    if not _pid_alive(pid):
        cleaned = _unlink_state(state_path)
        return ManagedTransportResult(
            transport,
            provider,
            "stale" if cleaned else "stale-cleanup-failed",
            endpoint,
            True,
            pid,
            state_dir,
            command,
            (
                f"removed stale AMPB-owned {transport} state"
                if cleaned
                else f"could not remove stale AMPB-owned {transport} state"
            ),
            provider_source=provider_source,
        )

    try:
        os.kill(pid, signal.SIGTERM)
    except OSError as exc:
        return ManagedTransportResult(
            transport,
            provider,
            "stop-failed",
            endpoint,
            True,
            pid,
            state_dir,
            command,
            f"could not stop AMPB-owned {transport}: {exc}",
            provider_source=provider_source,
        )

    deadline = time.monotonic() + wait_seconds
    while time.monotonic() <= deadline:
        if not _pid_alive(pid):
            cleaned = _unlink_state(state_path)
            return ManagedTransportResult(
                transport,
                provider,
                "stopped" if cleaned else "stopped-cleanup-failed",
                endpoint,
                True,
                pid,
                state_dir,
                command,
                (
                    f"stopped AMPB-owned {transport}"
                    if cleaned
                    else f"stopped AMPB-owned {transport} but could not remove state"
                ),
                provider_source=provider_source,
            )
        time.sleep(0.1)

    return ManagedTransportResult(
        transport,
        provider,
        "stop-timeout",
        endpoint,
        True,
        pid,
        state_dir,
        command,
        f"AMPB-owned {transport} did not stop before timeout",
        provider_source=provider_source,
    )


def repair_managed_transport(
    transport: str,
    *,
    config: AppConfig,
    root: Path,
    wait_seconds: float = 5.0,
) -> ManagedTransportResult:
    adapter = adapter_for(transport)
    if adapter is None:
        return ManagedTransportResult(transport, "-", "unsupported", "-", False, 0, "-", (), "transport adapter not found")

    state_dir = _managed_state_dir(root, config, transport)
    state_path = Path(state_dir)
    stop_result = stop_managed_transport(transport, config=config, root=root, wait_seconds=wait_seconds)
    if stop_result.status in {"stop-failed", "stop-timeout"}:
        return ManagedTransportResult(
            transport,
            stop_result.provider,
            "repair-blocked",
            stop_result.endpoint,
            stop_result.owned,
            stop_result.pid,
            state_dir,
            stop_result.command,
            f"could not repair AMPB-owned {transport}: {stop_result.message}",
            provider_source=stop_result.provider_source,
        )

    try:
        shutil.rmtree(state_path)
    except FileNotFoundError:
        pass
    except OSError as exc:
        return ManagedTransportResult(
            transport,
            stop_result.provider,
            "repair-failed",
            stop_result.endpoint,
            stop_result.owned,
            stop_result.pid,
            state_dir,
            stop_result.command,
            f"could not remove AMPB-owned {transport} runtime state: {exc}",
            provider_source=stop_result.provider_source,
        )

    return ManagedTransportResult(
        transport,
        stop_result.provider,
        "repaired",
        stop_result.endpoint,
        stop_result.owned,
        stop_result.pid,
        state_dir,
        stop_result.command,
        f"removed AMPB-owned {transport} runtime state; run `ampbrowser transport start {transport}` to rebuild it",
        provider_source=stop_result.provider_source,
    )


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
            provider_source=provider.source,
        )

    if _wait_for_endpoint(endpoint, timeout_seconds=wait_seconds):
        result = ManagedTransportResult(
            "tor",
            provider.kind,
            "started",
            endpoint,
            True,
            process.pid,
            state_dir,
            command,
            f"started managed {provider.kind} transport",
            provider_source=provider.source,
        )
        _write_owned_state(root, config, result)
        return result

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
        provider_source=provider.source,
    )


def _tor_provider(config: AppConfig) -> TorProvider | None:
    arti_path = os.environ.get("AMPB_ARTI_BIN")
    if arti_path:
        return TorProvider("arti", arti_path, "configured")

    tor_path = os.environ.get("AMPB_TOR_BIN")
    if tor_path:
        return TorProvider("tor", tor_path, "configured")

    config_path = config.transport_binary("tor")
    if config_path:
        return TorProvider(_infer_provider_kind(config_path), config_path, "configured")

    bundled_arti = _bundled_arti_path()
    if bundled_arti:
        return TorProvider("arti", bundled_arti, "bundled-sidecar")

    system_tor = shutil.which("tor")
    if system_tor:
        return TorProvider("tor", system_tor, "system-package")
    return None


def _bundled_arti_path() -> str:
    return _bundled_provider_path(ARTI_RELATIVE_PATH)


def _bundled_i2pd_path() -> str:
    return _bundled_provider_path(I2PD_RELATIVE_PATH)


def _bundled_provider_path(relative_path: Path) -> str:
    provider_root = os.environ.get("AMPB_PROVIDER_ROOT")
    if provider_root:
        candidate = Path(provider_root) / relative_path
        if candidate.exists() and candidate.is_file():
            return str(candidate)
    build_root = Path(os.environ.get("AMPB_BROWSER_BUILD_ROOT", "/tmp/ampb-browser-build"))
    candidate = build_root / relative_path
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


def _start_i2p(
    *,
    config: AppConfig,
    root: Path,
    endpoint: str,
    wait_seconds: float,
) -> ManagedTransportResult:
    provider = _i2p_provider(config)
    state_dir = _managed_state_dir(root, config, "i2p")
    if not provider:
        setup = _i2p_setup_hint()
        return ManagedTransportResult(
            "i2p",
            "-",
            "missing-provider",
            endpoint,
            False,
            0,
            state_dir,
            (),
            "I2P provider not found. " + setup.message,
            setup_hint=setup.message,
            install_command=setup.command,
        )

    state_path = Path(state_dir)
    state_path.mkdir(parents=True, exist_ok=True)
    _chmod_private(state_path)

    command = _i2p_command(provider, endpoint=endpoint, state_path=state_path)
    try:
        with (state_path / f"{provider.kind}.log").open("ab") as log_file:
            process = subprocess.Popen(command, stdout=log_file, stderr=log_file, start_new_session=True)  # noqa: S603
    except OSError as exc:
        return ManagedTransportResult(
            "i2p",
            provider.kind,
            "start-failed",
            endpoint,
            False,
            0,
            state_dir,
            command,
            f"managed {provider.kind} could not start: {exc}",
            provider_source=provider.source,
        )

    if _wait_for_endpoint(endpoint, timeout_seconds=wait_seconds):
        result = ManagedTransportResult(
            "i2p",
            provider.kind,
            "started",
            endpoint,
            True,
            process.pid,
            state_dir,
            command,
            f"started managed {provider.kind} transport",
            provider_source=provider.source,
        )
        _write_owned_state(root, config, result)
        return result

    process.terminate()
    return ManagedTransportResult(
        "i2p",
        provider.kind,
        "start-timeout",
        endpoint,
        True,
        process.pid,
        state_dir,
        command,
        f"managed {provider.kind} did not become ready at {endpoint}",
        provider_source=provider.source,
    )


def _i2p_provider(config: AppConfig) -> I2PProvider | None:
    env_path = os.environ.get("AMPB_I2PD_BIN")
    if env_path:
        return I2PProvider("i2pd", env_path, "configured")

    config_path = config.transport_binary("i2p")
    if config_path:
        return I2PProvider("i2pd", config_path, "configured")

    bundled_i2pd = _bundled_i2pd_path()
    if bundled_i2pd:
        return I2PProvider("i2pd", bundled_i2pd, "bundled-sidecar")

    system_i2pd = shutil.which("i2pd")
    if system_i2pd:
        return I2PProvider("i2pd", system_i2pd, "system-package")

    homebrew_i2pd = _homebrew_i2pd_path()
    if homebrew_i2pd:
        return I2PProvider("i2pd", homebrew_i2pd, "system-package")
    return None


def _stopped_setup_hint(transport: str, config: AppConfig) -> str:
    if transport == "i2p" and _i2p_provider(config) is None:
        return _i2p_setup_hint().message
    return "-"


def _stopped_install_command(transport: str, config: AppConfig) -> tuple[str, ...]:
    if transport == "i2p" and _i2p_provider(config) is None:
        return _i2p_setup_hint().command
    return ()


def _i2p_setup_hint() -> SetupHint:
    override = "Or set AMPB_I2PD_BIN or transports.i2p.binary_path to an i2pd binary."
    if sys.platform == "darwin":
        return SetupHint("Install i2pd with Homebrew: brew install i2pd. " + override, ("brew", "install", "i2pd"))
    if shutil.which("pkg"):
        return SetupHint("Install i2pd with pkg: pkg install i2pd. " + override, ("pkg", "install", "i2pd"))
    if shutil.which("apt"):
        return SetupHint("Install i2pd with apt: sudo apt install i2pd. " + override, ("sudo", "apt", "install", "i2pd"))
    if shutil.which("dnf"):
        return SetupHint("Install i2pd with dnf: sudo dnf install i2pd. " + override, ("sudo", "dnf", "install", "i2pd"))
    if shutil.which("pacman"):
        return SetupHint("Install i2pd with pacman: sudo pacman -S i2pd. " + override, ("sudo", "pacman", "-S", "i2pd"))
    return SetupHint("Install i2pd with your package manager. " + override)


def _homebrew_i2pd_path() -> str:
    brew = shutil.which("brew")
    if not brew:
        return ""
    try:
        result = subprocess.run(
            [brew, "--prefix", "i2pd"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=2,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    if result.returncode != 0:
        return ""
    prefix = Path(result.stdout.strip())
    for candidate in (prefix / "bin/i2pd", prefix / "sbin/i2pd"):
        if candidate.exists() and candidate.is_file():
            return str(candidate)
    return ""


def _i2p_command(provider: I2PProvider, *, endpoint: str, state_path: Path) -> tuple[str, ...]:
    host, port = _endpoint_host_port(endpoint)
    data_dir = state_path / "i2pd-data"
    data_dir.mkdir(parents=True, exist_ok=True)
    _chmod_private(data_dir)
    config_path = state_path / "i2pd.conf"
    tunnels_path = state_path / "tunnels.conf"
    tunnels_path.touch(exist_ok=True)
    config_path.write_text(_i2pd_config(host=host, port=port, state_path=state_path), encoding="utf-8")
    _chmod_private(config_path)
    _chmod_private(tunnels_path)
    return (
        provider.binary,
        "--conf",
        str(config_path),
        "--tunconf",
        str(tunnels_path),
        "--datadir",
        str(data_dir),
    )


def _i2pd_config(*, host: str, port: int, state_path: Path) -> str:
    return "\n".join(
        (
            "daemon = false",
            "service = false",
            "notransit = true",
            "log = file",
            f"logfile = {state_path / 'i2pd-router.log'}",
            "loglevel = warn",
            "",
            "[http]",
            "enabled = false",
            "",
            "[httpproxy]",
            "enabled = true",
            f"address = {host}",
            f"port = {port}",
            "addresshelper = true",
            "senduseragent = false",
            "",
            "[socksproxy]",
            "enabled = false",
            "",
            "[sam]",
            "enabled = false",
            "",
            "[bob]",
            "enabled = false",
            "",
            "[i2cp]",
            "enabled = false",
            "",
            "[i2pcontrol]",
            "enabled = false",
            "",
            "[upnp]",
            "enabled = false",
            "",
        )
    )


def _managed_state_dir(root: Path, config: AppConfig, transport: str) -> str:
    return str(root / config.state_dir / "transports" / transport)


def _owned_state_path(root: Path, config: AppConfig, transport: str) -> Path:
    return Path(_managed_state_dir(root, config, transport)) / OWNED_STATE_FILE


def _write_owned_state(root: Path, config: AppConfig, result: ManagedTransportResult) -> None:
    state_path = _owned_state_path(root, config, result.transport)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    _chmod_private(state_path.parent)
    data = {
        "transport": result.transport,
        "provider": result.provider,
        "endpoint": result.endpoint,
        "pid": result.pid,
        "state_dir": result.state_dir,
        "command": list(result.command),
        "provider_source": result.provider_source,
        "started_at": int(time.time()),
    }
    state_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _chmod_private(state_path)


def _owned_transport_result(
    transport: str,
    *,
    config: AppConfig,
    root: Path,
    wait_seconds: float,
) -> ManagedTransportResult | None:
    state_path = _owned_state_path(root, config, transport)
    state = _read_owned_state(state_path)
    if not state:
        return None

    pid = _state_pid(state)
    provider = str(state.get("provider") or "-")
    provider_source = str(state.get("provider_source") or "-")
    endpoint = str(state.get("endpoint") or _endpoint_for(transport))
    state_dir = str(state.get("state_dir") or _managed_state_dir(root, config, transport))
    command = tuple(str(part) for part in state.get("command", ()))

    if not pid or not _pid_alive(pid):
        cleaned = _unlink_state(state_path)
        return ManagedTransportResult(
            transport,
            provider,
            "stale" if cleaned else "stale-cleanup-failed",
            endpoint,
            True,
            pid,
            state_dir,
            command,
            (
                f"removed stale AMPB-owned {transport} state"
                if cleaned
                else f"could not remove stale AMPB-owned {transport} state"
            ),
            provider_source=provider_source,
        )

    if _wait_for_endpoint(endpoint, timeout_seconds=wait_seconds):
        return ManagedTransportResult(
            transport,
            provider,
            "ready",
            endpoint,
            True,
            pid,
            state_dir,
            command,
            f"using running AMPB-owned {transport}",
            provider_source=provider_source,
        )

    return ManagedTransportResult(
        transport,
        provider,
        "running",
        endpoint,
        True,
        pid,
        state_dir,
        command,
        f"AMPB-owned {transport} process is running but endpoint is not ready",
        provider_source=provider_source,
    )


def _read_owned_state(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    return data


def _state_pid(state: dict[str, object]) -> int:
    value = state.get("pid")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return 0


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _unlink_state(path: Path) -> bool:
    try:
        path.unlink()
        return True
    except FileNotFoundError:
        return True
    except OSError:
        return False


def _endpoint_for(transport: str) -> str:
    adapter = adapter_for(transport)
    if not adapter:
        return "-"
    return adapter.endpoint


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
