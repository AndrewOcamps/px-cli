from __future__ import annotations

import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
import requests_mock

from px_cli.client import ProxmoxClient
from px_cli.config import ProxmoxSettings


@pytest.fixture
def tmp_config_dir() -> Generator[Path, None, None]:
    with tempfile.TemporaryDirectory() as td:
        tmp_path = Path(td)
        # We patch via environment variables instead of file
        yield tmp_path


@pytest.fixture
def mock_client() -> ProxmoxClient:
    return ProxmoxClient(
        endpoint="https://proxmox.example.com:8006",
        token="user@pam!test=secret",
    )


@pytest.fixture
def requests_mocker() -> Generator[Any, None, None]:
    with requests_mock.Mocker() as m:
        yield m


@pytest.fixture
def sample_vm() -> dict[str, Any]:
    return {
        "vmid": 100,
        "name": "test-vm",
        "status": "running",
        "node": "pve1",
        "type": "qemu",
        "maxmem": 8589934592,
        "mem": 4294967296,
        "maxcpu": 4,
        "cpu": 0.5,
        "uptime": 3600,
    }


@pytest.fixture
def sample_config() -> ProxmoxSettings:
    return ProxmoxSettings(
        endpoint="https://192.168.1.100:8006",
        token="root@pam!mytoken=mysecret",
    )
