from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ProxmoxResource(BaseModel):
    vmid: int = 0
    name: str = ""
    status: str = ""
    node: str = ""
    pool: str | None = None
    type: str = ""
    maxmem: int = 0
    mem: int = 0
    maxdisk: int = 0
    disk: int = 0
    maxcpu: int = 0
    cpu: float = 0.0
    uptime: int = 0
    netin: int = 0
    netout: int = 0
    diskread: int = 0
    diskwrite: int = 0
    tags: str = ""
    id: str = ""
    storage: str = ""
    content: str = ""


class Snapshot(BaseModel):
    name: str = ""
    description: str = ""
    snaptime: int = 0
    vmstate: int = 0
    parent: str = ""
    children: list[dict[str, Any]] | None = None


class StorageInfo(BaseModel):
    storage: str = ""
    type: str = ""
    used: int = 0
    avail: int = 0
    total: int = 0
    content: str = ""
    node: str = ""


class StorageContent(BaseModel):
    volid: str = ""
    format: str = ""
    size: int = 0
    content: str = ""
    ctime: int = 0
    notes: str = ""


class PoolInfo(BaseModel):
    poolid: str = ""
    comment: str = ""
    members: list[Any] = Field(default_factory=list)


class NodeService(BaseModel):
    id: str = ""
    name: str = ""
    state: str = ""
    desc: str = ""


class BackupInfo(BaseModel):
    volid: str = ""
    size: int = 0
    ctime: int = 0
    notes: str = ""
    vmid: int = 0


class AplTemplate(BaseModel):
    template: str = ""
    os: str = ""
    version: str = ""
    description: str = ""
    location: str = ""
    headline: str = ""
    infotext: str = ""
    type: str = ""
    manage: int = 0
    status: str = ""
    package: str = ""


class FirewallRule(BaseModel):
    pos: int = 0
    type: str = ""
    action: str = ""
    enable: int = 0
    comment: str = ""
    dest: str = ""
    dport: str = ""
    iface: str = ""
    log: str = ""
    macro: str = ""
    proto: str = ""
    source: str = ""
    sport: str = ""
