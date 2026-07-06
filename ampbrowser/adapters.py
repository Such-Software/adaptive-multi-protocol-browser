from __future__ import annotations

from dataclasses import dataclass
import shutil
import socket


@dataclass(frozen=True)
class TransportStatus:
    transport: str
    installed: bool
    running: bool
    endpoint: str
    adoptable: bool
    manage_supported: bool
    note: str


@dataclass(frozen=True)
class TransportAdapter:
    name: str
    profile: str
    endpoint: str
    adopt_check: str
    managed_state: str
    install_strategy: str
    start_strategy: str
    stop_policy: str
    note: str
    commands: tuple[str, ...] = ()
    connect_host: str = ""
    connect_port: int = 0
    builtin_running: bool = False
    manage_supported: bool = True

    def inspect(self) -> TransportStatus:
        installed = self.builtin_running or any(shutil.which(command) for command in self.commands)
        running = self.builtin_running or (
            bool(self.connect_host) and bool(self.connect_port) and _can_connect(self.connect_host, self.connect_port)
        )
        return TransportStatus(
            transport=self.name,
            installed=installed,
            running=running,
            endpoint=self.endpoint,
            adoptable=running,
            manage_supported=self.manage_supported,
            note=self.note,
        )

    def setup_steps(self, *, installed: bool, platform: str) -> tuple[str, ...]:
        steps: list[str] = []
        if not installed and self.install_strategy != "unsupported":
            steps.append(self.install_strategy)
        if platform == "android":
            steps.append(f"start visible Android foreground service for {self.name}")
            steps.append(f"start managed Android {self.name} transport")
            steps.append(f"wait for {self.endpoint}")
            return tuple(steps)
        elif platform == "ios":
            steps.append(f"start foreground-only iOS session for {self.name}")
            steps.append(f"start foreground-only iOS {self.name} transport")
            steps.append(f"wait for {self.endpoint}")
            return tuple(steps)
        if self.start_strategy != "unsupported":
            steps.append(self.start_strategy)
        steps.append(f"wait for {self.endpoint}")
        return tuple(steps)


ADAPTERS: dict[str, TransportAdapter] = {
    "tor": TransportAdapter(
        name="tor",
        profile="tor",
        endpoint="socks5://127.0.0.1:9050",
        adopt_check="SOCKS on 127.0.0.1:9050",
        managed_state=".ampb/transports/tor",
        install_strategy="install Tor provider",
        start_strategy="start managed Tor daemon",
        stop_policy="stop only AMPB-owned Tor daemon",
        note="Tor SOCKS proxy",
        commands=("tor",),
        connect_host="127.0.0.1",
        connect_port=9050,
    ),
    "i2p": TransportAdapter(
        name="i2p",
        profile="i2p",
        endpoint="http://127.0.0.1:4444",
        adopt_check="HTTP proxy on 127.0.0.1:4444",
        managed_state=".ampb/transports/i2p",
        install_strategy="install I2P provider",
        start_strategy="start managed I2P router",
        stop_policy="stop only AMPB-owned I2P router",
        note="I2P HTTP proxy",
        commands=("i2pd", "i2prouter"),
        connect_host="127.0.0.1",
        connect_port=4444,
    ),
    "reticulum": TransportAdapter(
        name="reticulum",
        profile="reticulum",
        endpoint="rns://local",
        adopt_check="RNS tools and configured interfaces",
        managed_state=".ampb/transports/reticulum",
        install_strategy="install Reticulum provider",
        start_strategy="start configured Reticulum interface",
        stop_policy="stop only AMPB-owned Reticulum process",
        note="Reticulum adapter is planned for resilient/private routing; it is not an anonymity layer",
        commands=("rnsd", "rnstatus", "rnodeconf"),
        manage_supported=False,
    ),
    "ipfs": TransportAdapter(
        name="ipfs",
        profile="ipfs",
        endpoint="http://127.0.0.1:8080",
        adopt_check="HTTP gateway on 127.0.0.1:8080",
        managed_state=".ampb/transports/ipfs",
        install_strategy="install IPFS/Kubo provider",
        start_strategy="start managed IPFS gateway",
        stop_policy="stop only AMPB-owned IPFS process",
        note="IPFS local gateway for content-addressed distribution; not an anonymity layer",
        commands=("ipfs",),
        connect_host="127.0.0.1",
        connect_port=8080,
    ),
    "gemini": TransportAdapter(
        name="gemini",
        profile="gemini",
        endpoint="builtin://gemtext-renderer",
        adopt_check="built-in renderer available",
        managed_state=".ampb/transports/gemini",
        install_strategy="unsupported",
        start_strategy="use built-in Gemtext fetch/render path",
        stop_policy="no daemon to stop",
        note="Built-in Gemtext fetch/render path",
        builtin_running=True,
    ),
}


def adapter_for(name: str) -> TransportAdapter | None:
    return ADAPTERS.get(name)


def _can_connect(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.2):
            return True
    except OSError:
        return False
