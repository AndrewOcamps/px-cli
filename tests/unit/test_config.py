from __future__ import annotations

from px_cli.config import ProxmoxSettings


class TestProxmoxSettings:
    def test_default_values(self):
        settings = ProxmoxSettings()
        assert settings.endpoint == ""
        assert settings.token == ""

    def test_from_env_vars(self, monkeypatch):
        monkeypatch.setenv("PX_ENDPOINT", "https://192.168.1.100:8006")
        monkeypatch.setenv("PX_TOKEN", "root@pam!token=secret")
        settings = ProxmoxSettings()
        assert settings.endpoint == "https://192.168.1.100:8006"
        assert settings.token == "root@pam!token=secret"

    def test_env_override_file(self, monkeypatch, tmp_path):
        monkeypatch.setenv("PX_ENDPOINT", "https://env:8006")
        monkeypatch.setenv("PX_TOKEN", "env!token=secret")
        config_file = tmp_path / "config"
        config_file.write_text("endpoint=https://file:8006\ntoken=file!token=secret\n")

        settings = ProxmoxSettings(_env_file=str(tmp_path / ".env"))
        # No file set, so defaults to env vars
        assert settings.endpoint == "https://env:8006"

    def test_validate_raises_on_missing_endpoint(self):
        settings = ProxmoxSettings(token="some-token")
        import pytest

        from px_cli.exceptions import ConfigError

        with pytest.raises(ConfigError, match="endpoint"):
            settings.validate_config()

    def test_validate_raises_on_missing_token(self):
        settings = ProxmoxSettings(endpoint="https://example.com:8006")
        import pytest

        from px_cli.exceptions import ConfigError

        with pytest.raises(ConfigError, match="token"):
            settings.validate_config()

    def test_validate_passes(self, sample_config):
        sample_config.validate_config()


class TestLoadConfig:
    def test_load_from_file(self, tmp_path, monkeypatch):
        config_dir = tmp_path / ".proxmox"
        config_dir.mkdir()
        config_file = config_dir / "config"
        config_file.write_text("endpoint=https://192.168.1.100:8006\ntoken=root@pam!token=secret\n")

        monkeypatch.setattr("px_cli.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("px_cli.config.CONFIG_PATH", config_file)

        from px_cli.config import load_config

        settings = load_config()
        assert settings.endpoint == "https://192.168.1.100:8006"
        assert settings.token == "root@pam!token=secret"

    def test_env_var_overrides_file(self, tmp_path, monkeypatch):
        config_dir = tmp_path / ".proxmox"
        config_dir.mkdir()
        config_file = config_dir / "config"
        config_file.write_text("endpoint=https://file:8006\ntoken=file!token=secret\n")

        monkeypatch.setattr("px_cli.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("px_cli.config.CONFIG_PATH", config_file)
        monkeypatch.setenv("PX_ENDPOINT", "https://env:8006")

        from px_cli.config import load_config

        settings = load_config()
        assert settings.endpoint == "https://env:8006"
        assert settings.token == "file!token=secret"


class TestWriteConfig:
    def test_write_config_creates_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("px_cli.config.CONFIG_DIR", tmp_path)
        monkeypatch.setattr("px_cli.config.CONFIG_PATH", tmp_path / "config")

        from px_cli.config import write_config

        path = write_config("https://example.com:8006", "user!token=secret")
        assert path.exists()
        content = path.read_text()
        assert "endpoint=https://example.com:8006" in content
        assert "token=user!token=secret" in content


class TestRemoveConfig:
    def test_remove_config_creates_backup(self, tmp_path, monkeypatch):
        config_dir = tmp_path / ".proxmox"
        config_dir.mkdir()
        config_file = config_dir / "config"
        config_file.write_text("endpoint=https://example.com:8006\ntoken=x\n")

        monkeypatch.setattr("px_cli.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("px_cli.config.CONFIG_PATH", config_file)

        from px_cli.config import remove_config

        backup = remove_config()
        assert not config_file.exists()
        assert backup.exists()
        assert backup.name == "config.bak"
