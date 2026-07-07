from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on older Python versions
    tomllib = None  # type: ignore[assignment]


DEFAULT_CONFIG_PATH = Path(".ampb/config.toml")
DEFAULT_TRANSPORT_MODE = "adopt-or-prompt-manage"
TRANSPORT_MODES = {"disabled", "adopt", "adopt-or-prompt-manage"}
MODE_ALIASES = {"adopt-or-manage": "adopt-or-prompt-manage"}


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class AppConfig:
    state_dir: str = ".ampb"
    default_engine: str = "ampb-gecko"
    runtime_path: str = ""
    isolate_by_transport: bool = True
    transport_modes: dict[str, str] | None = None

    def transport_mode(self, transport: str) -> str:
        if not self.transport_modes:
            return DEFAULT_TRANSPORT_MODE
        return self.transport_modes.get(transport, DEFAULT_TRANSPORT_MODE)

    def profile_path(self, profile: str) -> str:
        if self.isolate_by_transport:
            return str(Path(self.state_dir) / "profiles" / profile)
        return str(Path(self.state_dir) / "profile")


def default_config() -> AppConfig:
    return AppConfig(transport_modes={})


def load_config(root: Path | None = None, config_path: Path | None = None) -> AppConfig:
    root = root or Path.cwd()
    path = config_path or root / DEFAULT_CONFIG_PATH
    if not path.exists():
        return default_config()

    text = path.read_text(encoding="utf-8")
    if tomllib:
        try:
            data = tomllib.loads(text)
        except tomllib.TOMLDecodeError as exc:
            raise ConfigError(f"invalid TOML in {path}: {exc}") from exc
    else:
        data = _loads_simple_toml(text, path)

    if not isinstance(data, dict):
        raise ConfigError(f"{path}: top-level config must be a table")
    return _parse_config(data, path)


def _parse_config(data: dict[str, Any], path: Path) -> AppConfig:
    browser = _table(data, "browser", path)
    profiles = _table(data, "profiles", path)
    transports = _table(data, "transports", path)

    state_dir = _string(browser, "state_dir", ".ampb", path)
    default_engine = _string(browser, "default_engine", "ampb-gecko", path)
    runtime_path = _string(browser, "runtime_path", "", path)
    isolate_by_transport = _bool(profiles, "isolate_by_transport", True, path)
    transport_modes = _transport_modes(transports, path)

    return AppConfig(
        state_dir=state_dir,
        default_engine=default_engine,
        runtime_path=runtime_path,
        isolate_by_transport=isolate_by_transport,
        transport_modes=transport_modes,
    )


def _transport_modes(transports: dict[str, Any], path: Path) -> dict[str, str]:
    modes: dict[str, str] = {}
    for name, raw_config in transports.items():
        if not isinstance(raw_config, dict):
            raise ConfigError(f"{path}: transports.{name} must be a table")

        enabled = raw_config.get("enabled", True)
        if not isinstance(enabled, bool):
            raise ConfigError(f"{path}: transports.{name}.enabled must be true or false")
        if not enabled:
            modes[name] = "disabled"
            continue

        raw_mode = raw_config.get("mode", DEFAULT_TRANSPORT_MODE)
        if not isinstance(raw_mode, str):
            raise ConfigError(f"{path}: transports.{name}.mode must be a string")
        mode = MODE_ALIASES.get(raw_mode, raw_mode)
        if mode not in TRANSPORT_MODES:
            choices = ", ".join(sorted(TRANSPORT_MODES))
            raise ConfigError(f"{path}: transports.{name}.mode must be one of: {choices}")
        modes[name] = mode
    return modes


def _table(data: dict[str, Any], key: str, path: Path) -> dict[str, Any]:
    value = data.get(key, {})
    if not isinstance(value, dict):
        raise ConfigError(f"{path}: {key} must be a table")
    return value


def _string(data: dict[str, Any], key: str, default: str, path: Path) -> str:
    value = data.get(key, default)
    if not isinstance(value, str):
        raise ConfigError(f"{path}: {key} must be a string")
    return value


def _bool(data: dict[str, Any], key: str, default: bool, path: Path) -> bool:
    value = data.get(key, default)
    if not isinstance(value, bool):
        raise ConfigError(f"{path}: {key} must be true or false")
    return value


def _loads_simple_toml(text: str, path: Path) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current = data
    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        line = _strip_comment(raw_line).strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            current = _table_for_header(data, line[1:-1].strip(), path, lineno)
            continue
        if "=" not in line:
            raise ConfigError(f"{path}:{lineno}: expected key = value")
        key, raw_value = line.split("=", 1)
        key = key.strip()
        if not key:
            raise ConfigError(f"{path}:{lineno}: empty key")
        current[key] = _parse_simple_value(raw_value.strip(), path, lineno)
    return data


def _table_for_header(data: dict[str, Any], header: str, path: Path, lineno: int) -> dict[str, Any]:
    if not header:
        raise ConfigError(f"{path}:{lineno}: empty table name")
    current = data
    for part in header.split("."):
        if not part:
            raise ConfigError(f"{path}:{lineno}: invalid table name")
        existing = current.setdefault(part, {})
        if not isinstance(existing, dict):
            raise ConfigError(f"{path}:{lineno}: table conflicts with value: {header}")
        current = existing
    return current


def _parse_simple_value(value: str, path: Path, lineno: int) -> str | bool:
    if value == "true":
        return True
    if value == "false":
        return False
    if len(value) >= 2 and value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    raise ConfigError(f"{path}:{lineno}: only strings and booleans are supported")


def _strip_comment(line: str) -> str:
    in_string = False
    escaped = False
    for index, char in enumerate(line):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if char == "#" and not in_string:
            return line[:index]
    return line
