from __future__ import annotations

from px_cli.models import (
    AplTemplate,
    BackupInfo,
    FirewallRule,
    NodeService,
    PoolInfo,
    ProxmoxResource,
    Snapshot,
    StorageContent,
    StorageInfo,
)


class TestProxmoxResource:
    def test_defaults(self):
        r = ProxmoxResource()
        assert r.vmid == 0
        assert r.name == ""
        assert r.status == ""
        assert r.pool is None

    def test_from_dict(self, sample_vm):
        r = ProxmoxResource(**sample_vm)
        assert r.vmid == 100
        assert r.name == "test-vm"
        assert r.status == "running"
        assert r.node == "pve1"
        assert r.type == "qemu"
        assert r.maxmem == 8589934592

    def test_to_dict(self, sample_vm):
        r = ProxmoxResource(**sample_vm)
        d = r.model_dump()
        assert d["vmid"] == 100
        assert d["name"] == "test-vm"


class TestSnapshot:
    def test_defaults(self):
        s = Snapshot()
        assert s.name == ""
        assert s.snaptime == 0
        assert s.children is None

    def test_with_children(self):
        s = Snapshot(name="snap1", children=[{"name": "child1"}])
        assert s.name == "snap1"
        assert s.children == [{"name": "child1"}]


class TestStorageInfo:
    def test_defaults(self):
        s = StorageInfo()
        assert s.storage == ""
        assert s.type == ""


class TestStorageContent:
    def test_defaults(self):
        s = StorageContent()
        assert s.volid == ""
        assert s.format == ""


class TestPoolInfo:
    def test_defaults(self):
        p = PoolInfo()
        assert p.poolid == ""
        assert p.members == []


class TestNodeService:
    def test_defaults(self):
        n = NodeService()
        assert n.id == ""
        assert n.state == ""


class TestBackupInfo:
    def test_defaults(self):
        b = BackupInfo()
        assert b.volid == ""
        assert b.vmid == 0


class TestAplTemplate:
    def test_defaults(self):
        t = AplTemplate()
        assert t.template == ""
        assert t.os == ""


class TestFirewallRule:
    def test_defaults(self):
        f = FirewallRule()
        assert f.pos == 0
        assert f.action == ""
