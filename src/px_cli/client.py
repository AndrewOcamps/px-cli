import time
import urllib.parse
from typing import Any

import requests
import urllib3

from .exceptions import ApiError

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class ProxmoxClient:
    def __init__(
        self,
        endpoint: str,
        token: str | None = None,
        ticket: str | None = None,
        csrf_token: str | None = None,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        self.endpoint = endpoint.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.verify = False

        if token:
            self.session.headers.update({"Authorization": f"PVEAPIToken={token}"})
        if ticket:
            self.session.cookies.set("PVEAuthCookie", ticket)
        if csrf_token:
            self.session.headers.update({"CSRFPreventionToken": csrf_token})

    def __enter__(self) -> "ProxmoxClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.session.close()

    def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> Any:
        url = f"{self.endpoint}{path}"
        kwargs.setdefault("timeout", self.timeout)

        for attempt in range(self.max_retries):
            try:
                resp = self.session.request(method, url, **kwargs)
                resp.raise_for_status()
                return resp.json().get("data")
            except requests.RequestException as e:
                if attempt == self.max_retries - 1:
                    status = e.response.status_code if e.response is not None else 0
                    msg = str(e)
                    if e.response is not None:
                        try:
                            msg = e.response.json().get("errors", str(e))
                        except Exception:
                            msg = e.response.text[:200]
                    raise ApiError(status, msg) from e
                time.sleep(2 ** attempt)

    # ── Authentication ──────────────────────────────────────────────

    def login(self, username: str, password: str) -> dict:
        url = f"{self.endpoint}/api2/json/access/ticket"
        resp = self.session.post(url, data={"username": username, "password": password})
        resp.raise_for_status()
        data = resp.json()["data"]
        self.session.cookies.set("PVEAuthCookie", data["ticket"])
        self.session.headers.update({"CSRFPreventionToken": data["CSRFPreventionToken"]})
        return data

    def create_token(self, user: str, token_id: str, comment: str = "") -> dict:
        data: dict[str, str] = {"id": token_id}
        if comment:
            data["comment"] = comment
        return self.raw_post(f"/api2/json/access/users/{user}/token", data=data)

    def whoami(self) -> dict:
        return self.raw_get("/api2/json/access/ticket")

    # ── Raw API ─────────────────────────────────────────────────────

    def raw_get(self, path: str, params: dict | None = None) -> Any:
        return self._request("GET", path, params=params)

    def raw_post(self, path: str, data: dict | None = None) -> Any:
        result = self._request("POST", path, data=data)
        if isinstance(result, str):
            return {"upid": result}
        return result or {}

    def raw_put(self, path: str, data: dict | None = None) -> Any:
        return self._request("PUT", path, data=data) or {}

    def raw_delete(self, path: str) -> Any:
        return self._request("DELETE", path) or {}

    # ── Listing / Resources ─────────────────────────────────────────

    def list_resources(self, resource_type: str | None = None) -> list:
        params = {}
        if resource_type:
            params["type"] = resource_type
        return self.raw_get("/api2/json/cluster/resources", params=params)

    def list_vms(self) -> list:
        return [r for r in self.list_resources("vm") if r.get("type") == "qemu"]

    def list_containers(self) -> list:
        return [r for r in self.list_resources("vm") if r.get("type") == "lxc"]

    # ── Lookup ──────────────────────────────────────────────────────

    def find_resource(self, vmid: int) -> dict | None:
        data = self.list_resources("vm")
        return next((r for r in data if r.get("vmid") == vmid), None)

    # ── VM / CT Actions ─────────────────────────────────────────────

    def perform_action(self, node: str, vmtype: str, vmid: int, action_name: str) -> dict:
        return self.raw_post(
            f"/api2/json/nodes/{node}/{vmtype}/{vmid}/status/{action_name}"
        )

    def start(self, node: str, vmtype: str, vmid: int) -> dict:
        return self.perform_action(node, vmtype, vmid, "start")

    def stop(self, node: str, vmtype: str, vmid: int) -> dict:
        return self.perform_action(node, vmtype, vmid, "stop")

    def shutdown(self, node: str, vmtype: str, vmid: int) -> dict:
        return self.perform_action(node, vmtype, vmid, "shutdown")

    def reboot(self, node: str, vmtype: str, vmid: int) -> dict:
        return self.perform_action(node, vmtype, vmid, "reboot")

    def suspend(self, node: str, vmtype: str, vmid: int) -> dict:
        return self.perform_action(node, vmtype, vmid, "suspend")

    def resume(self, node: str, vmtype: str, vmid: int) -> dict:
        return self.perform_action(node, vmtype, vmid, "resume")

    def get_detail(self, node: str, vmtype: str, vmid: int) -> dict:
        return self.raw_get(
            f"/api2/json/nodes/{node}/{vmtype}/{vmid}/status/current"
        )

    def get_config(self, node: str, vmtype: str, vmid: int) -> dict:
        return self.raw_get(f"/api2/json/nodes/{node}/{vmtype}/{vmid}/config")

    # ── Task Polling ────────────────────────────────────────────────

    def wait_for_task(self, node: str, upid: str, timeout: int = 120) -> bool:
        encoded_upid = urllib.parse.quote(upid, safe="")
        for _ in range(timeout * 2):
            data = self.raw_get(
                f"/api2/json/nodes/{node}/tasks/{encoded_upid}/status"
            )
            if data.get("status") == "stopped":
                exit_code = data.get("exitstatus", "")
                return exit_code == "OK" or exit_code == ""
            time.sleep(0.5)
        return False

    # ── Snapshots ───────────────────────────────────────────────────

    def list_snapshots(self, node: str, vmtype: str, vmid: int) -> list:
        return self.raw_get(f"/api2/json/nodes/{node}/{vmtype}/{vmid}/snapshot")

    def create_snapshot(
        self,
        node: str,
        vmtype: str,
        vmid: int,
        snapname: str,
        description: str = "",
        vmstate: bool = False,
    ) -> dict:
        data: dict[str, Any] = {"snapname": snapname}
        if description:
            data["description"] = description
        if vmstate:
            data["vmstate"] = 1
        return self.raw_post(
            f"/api2/json/nodes/{node}/{vmtype}/{vmid}/snapshot", data=data
        )

    def delete_snapshot(self, node: str, vmtype: str, vmid: int, snapname: str) -> dict:
        return self.raw_delete(
            f"/api2/json/nodes/{node}/{vmtype}/{vmid}/snapshot/{snapname}"
        )

    def rollback_snapshot(self, node: str, vmtype: str, vmid: int, snapname: str) -> dict:
        return self.raw_post(
            f"/api2/json/nodes/{node}/{vmtype}/{vmid}/snapshot/{snapname}/rollback"
        )

    # ── Storage ─────────────────────────────────────────────────────

    def list_storages(self) -> list:
        return self.raw_get("/api2/json/storage")

    def storage_content(self, storage: str, node: str) -> list:
        return self.raw_get(
            f"/api2/json/nodes/{node}/storage/{storage}/content"
        )

    # ── Templates (LXC) ─────────────────────────────────────────────

    def list_templates(self, node: str) -> list:
        return self.raw_get(f"/api2/json/nodes/{node}/aplinfo")

    def download_template(self, node: str, template: str) -> dict:
        return self.raw_post(
            f"/api2/json/nodes/{node}/aplinfo", data={"template": template}
        )

    # ── Backups ─────────────────────────────────────────────────────

    def create_backup(
        self,
        node: str,
        vmid: int,
        storage: str = "local",
        mode: str = "snapshot",
        compress: str = "zstd",
    ) -> dict:
        return self.raw_post(
            f"/api2/json/nodes/{node}/vzdump",
            data={
                "vmid": vmid,
                "storage": storage,
                "mode": mode,
                "compress": compress,
            },
        )

    # ── Pools ───────────────────────────────────────────────────────

    def list_pools(self) -> list:
        return self.raw_get("/api2/json/pools")

    def get_pool(self, pool_id: str) -> dict:
        return self.raw_get(f"/api2/json/pools/{pool_id}")

    def create_pool(self, pool_id: str, comment: str = "") -> dict:
        data: dict[str, str] = {"poolid": pool_id}
        if comment:
            data["comment"] = comment
        return self.raw_post("/api2/json/pools", data=data)

    def update_pool(self, pool_id: str, data: dict) -> dict:
        return self.raw_put(f"/api2/json/pools/{pool_id}", data=data)

    def delete_pool(self, pool_id: str) -> dict:
        return self.raw_delete(f"/api2/json/pools/{pool_id}")

    # ── Nodes ───────────────────────────────────────────────────────

    def get_node_status(self, node: str) -> dict:
        return self.raw_get(f"/api2/json/nodes/{node}/status")

    def get_node_version(self, node: str) -> dict:
        return self.raw_get(f"/api2/json/nodes/{node}/version")

    def list_node_services(self, node: str) -> list:
        return self.raw_get(f"/api2/json/nodes/{node}/services")

    def reboot_node(self, node: str) -> dict:
        return self.raw_post(
            f"/api2/json/nodes/{node}/status", data={"command": "reboot"}
        )

    # ── Cluster ─────────────────────────────────────────────────────

    def cluster_status(self) -> list:
        return self.raw_get("/api2/json/cluster/status")

    def cluster_log(self, max_items: int = 50) -> list:
        return self.raw_get("/api2/json/cluster/log", params={"max": max_items})

    def cluster_next_id(self) -> int:
        return self.raw_get("/api2/json/cluster/nextid")

    # ── Firewall ────────────────────────────────────────────────────

    def get_firewall_rules(
        self,
        node: str,
        vmtype: str | None = None,
        vmid: int | None = None,
    ) -> list:
        if vmtype and vmid:
            return self.raw_get(
                f"/api2/json/nodes/{node}/{vmtype}/{vmid}/firewall/rules"
            )
        return self.raw_get(f"/api2/json/nodes/{node}/firewall/rules")
