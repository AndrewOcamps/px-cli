from __future__ import annotations

from px_cli.exceptions import ApiError


class TestProxmoxClientInit:
    def test_init_with_token(self, mock_client):
        assert mock_client.endpoint == "https://proxmox.example.com:8006"
        assert mock_client.session.headers["Authorization"] == "PVEAPIToken=user@pam!test=secret"

    def test_init_strips_trailing_slash(self):
        from px_cli.client import ProxmoxClient

        client = ProxmoxClient("https://example.com:8006/", token="x")
        assert client.endpoint == "https://example.com:8006"

    def test_context_manager(self, mock_client):
        with mock_client as cm:
            assert cm is mock_client


class TestProxmoxClientRequests:
    def test_raw_get_success(self, requests_mocker, mock_client):
        requests_mocker.get(
            "https://proxmox.example.com:8006/api2/json/cluster/status",
            json={"data": [{"id": "cluster-1"}]},
        )
        result = mock_client.raw_get("/api2/json/cluster/status")
        assert result == [{"id": "cluster-1"}]

    def test_raw_get_with_params(self, requests_mocker, mock_client):
        requests_mocker.get(
            "https://proxmox.example.com:8006/api2/json/cluster/resources",
            json={"data": [{"vmid": 100}]},
        )
        result = mock_client.raw_get("/api2/json/cluster/resources", params={"type": "vm"})
        assert result == [{"vmid": 100}]

    def test_raw_post_returns_upid(self, requests_mocker, mock_client):
        requests_mocker.post(
            "https://proxmox.example.com:8006/api2/json/nodes/pve1/qemu/100/status/start",
            json={"data": "UPID:pve1:0001:..."},
        )
        result = mock_client.raw_post("/api2/json/nodes/pve1/qemu/100/status/start")
        assert result == {"upid": "UPID:pve1:0001:..."}

    def test_raw_put_success(self, requests_mocker, mock_client):
        requests_mocker.put(
            "https://proxmox.example.com:8006/api2/json/pools/my-pool",
            json={"data": {}},
        )
        result = mock_client.raw_put("/api2/json/pools/my-pool", data={"comment": "test"})
        assert result == {}

    def test_raw_delete_success(self, requests_mocker, mock_client):
        requests_mocker.delete(
            "https://proxmox.example.com:8006/api2/json/pools/my-pool",
            json={"data": {}},
        )
        result = mock_client.raw_delete("/api2/json/pools/my-pool")
        assert result == {}

    def test_api_error_raised(self, requests_mocker, mock_client):
        requests_mocker.get(
            "https://proxmox.example.com:8006/api2/json/cluster/status",
            status_code=500,
            json={"errors": "Internal server error"},
        )
        import pytest

        with pytest.raises(ApiError) as exc_info:
            mock_client.raw_get("/api2/json/cluster/status")
        assert exc_info.value.status_code == 500

    def test_not_found_error(self, requests_mocker, mock_client):
        requests_mocker.get(
            "https://proxmox.example.com:8006/api2/json/nodes/pve1/qemu/9999/status/current",
            status_code=404,
            json={"errors": "VM not found"},
        )
        import pytest

        with pytest.raises(ApiError) as exc_info:
            mock_client.raw_get("/api2/json/nodes/pve1/qemu/9999/status/current")
        assert exc_info.value.status_code == 404


class TestProxmoxClientActions:
    def test_list_vms(self, requests_mocker, mock_client):
        requests_mocker.get(
            "https://proxmox.example.com:8006/api2/json/cluster/resources",
            json={
                "data": [
                    {
                        "vmid": 100, "type": "qemu", "name": "vm1",
                        "status": "running", "node": "pve1",
                    },
                    {
                        "vmid": 200, "type": "lxc", "name": "ct1",
                        "status": "stopped", "node": "pve1",
                    },
                ]
            },
        )
        vms = mock_client.list_vms()
        assert len(vms) == 1
        assert vms[0]["vmid"] == 100

    def test_list_containers(self, requests_mocker, mock_client):
        requests_mocker.get(
            "https://proxmox.example.com:8006/api2/json/cluster/resources",
            json={
                "data": [
                    {
                        "vmid": 100, "type": "qemu", "name": "vm1",
                        "status": "running", "node": "pve1",
                    },
                    {
                        "vmid": 200, "type": "lxc", "name": "ct1",
                        "status": "stopped", "node": "pve1",
                    },
                ]
            },
        )
        containers = mock_client.list_containers()
        assert len(containers) == 1
        assert containers[0]["vmid"] == 200

    def test_find_resource(self, requests_mocker, mock_client):
        requests_mocker.get(
            "https://proxmox.example.com:8006/api2/json/cluster/resources",
            json={
                "data": [
                    {
                        "vmid": 100, "type": "qemu", "name": "vm1",
                        "status": "running", "node": "pve1",
                    },
                ]
            },
        )
        found = mock_client.find_resource(100)
        assert found is not None
        assert found["vmid"] == 100

        not_found = mock_client.find_resource(999)
        assert not_found is None

    def test_perform_action(self, requests_mocker, mock_client):
        requests_mocker.post(
            "https://proxmox.example.com:8006/api2/json/nodes/pve1/qemu/100/status/start",
            json={"data": "UPID:pve1:0001:..."},
        )
        result = mock_client.start("pve1", "qemu", 100)
        assert result["upid"] == "UPID:pve1:0001:..."

    def test_login(self, requests_mocker, mock_client):
        requests_mocker.post(
            "https://proxmox.example.com:8006/api2/json/access/ticket",
            json={
                "data": {
                    "ticket": "PVE:ticket...",
                    "CSRFPreventionToken": "csrf:token...",
                }
            },
        )
        data = mock_client.login("root@pam", "secret")
        assert data["ticket"] == "PVE:ticket..."
