from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ampbrowser.config import ConfigError, load_config


class ConfigTest(unittest.TestCase):
    def test_missing_config_uses_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = load_config(Path(tmp))

        self.assertEqual(".ampb", config.state_dir)
        self.assertEqual("hardened-firefox", config.default_engine)
        self.assertEqual("adopt-or-prompt-manage", config.transport_mode("tor"))
        self.assertEqual(".ampb/profiles/tor", config.profile_path("tor"))

    def test_loads_transport_modes_and_state_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.toml"
            path.write_text(
                """
[browser]
state_dir = ".local/ampb"

[transports.tor]
mode = "adopt"

[transports.i2p]
enabled = false
""".strip(),
                encoding="utf-8",
            )

            config = load_config(Path(tmp), path)

        self.assertEqual(".local/ampb", config.state_dir)
        self.assertEqual("adopt", config.transport_mode("tor"))
        self.assertEqual("disabled", config.transport_mode("i2p"))
        self.assertEqual(".local/ampb/profiles/i2p", config.profile_path("i2p"))

    def test_accepts_adopt_or_manage_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.toml"
            path.write_text(
                """
[transports.tor]
mode = "adopt-or-manage"
""".strip(),
                encoding="utf-8",
            )

            config = load_config(Path(tmp), path)

        self.assertEqual("adopt-or-prompt-manage", config.transport_mode("tor"))

    def test_rejects_unknown_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.toml"
            path.write_text(
                """
[transports.tor]
mode = "surprise"
""".strip(),
                encoding="utf-8",
            )

            with self.assertRaises(ConfigError):
                load_config(Path(tmp), path)


if __name__ == "__main__":
    unittest.main()
