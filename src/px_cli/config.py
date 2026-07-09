import os
import platform
import stat
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from .exceptions import ConfigError

CONFIG_DIR = Path.home() / ".proxmox"
CONFIG_PATH = CONFIG_DIR / "config"


class ProxmoxSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PX_",
        env_file=".env",
        extra="ignore",
    )

    endpoint: str = ""
    token: str = ""

    @classmethod
    def from_file(cls) -> "ProxmoxSettings":
        settings = cls()
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        # Only apply file value if no env var is set
                        if key == "endpoint" and "PX_ENDPOINT" not in os.environ:
                            settings.endpoint = value.strip()
                        elif key == "token" and "PX_TOKEN" not in os.environ:
                            settings.token = value.strip()
        return settings

    def validate_config(self) -> None:
        if not self.endpoint:
            raise ConfigError(
                "Proxmox endpoint not configured.\n"
                f"  Set it in {CONFIG_PATH} (endpoint=<url>)\n"
                "  or use PX_ENDPOINT environment variable."
            )
        if not self.token:
            raise ConfigError(
                "Proxmox token not configured.\n"
                f"  Set it in {CONFIG_PATH} (token=<id>=<secret>)\n"
                "  or use PX_TOKEN environment variable."
            )


def load_config() -> ProxmoxSettings:
    config = ProxmoxSettings.from_file()
    config.validate_config()
    return config


def write_config(endpoint: str, token: str) -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(f"endpoint={endpoint}\ntoken={token}\n")
    if platform.system() != "Windows":
        CONFIG_PATH.chmod(stat.S_IRUSR | stat.S_IWUSR)
    return CONFIG_PATH


def remove_config() -> Path:
    backup = CONFIG_PATH.with_suffix(CONFIG_PATH.suffix + ".bak")
    if CONFIG_PATH.exists():
        if backup.exists():
            backup.unlink()
        CONFIG_PATH.rename(backup)
    return backup
