import fnmatch
import json
from collections.abc import Callable
from typing import Any

import typer
from rich.console import Console
from rich.style import Style
from rich.table import Table
from rich.text import Text

from .client import ProxmoxClient
from .config import load_config

CONSOLE = Console()
COLOR_STYLES: dict[str, Style] = {
    "running": Style(color="green", bold=True),
    "stopped": Style(color="red"),
    "error": Style(color="yellow", bold=True),
}


def get_client() -> ProxmoxClient:
    config = load_config()
    return ProxmoxClient(config.endpoint, config.token)


def resolve_vmids(
    vmid_list: list[int], client: ProxmoxClient
) -> tuple[list[dict], list[str]]:
    results: list[dict] = []
    errors: list[str] = []
    for vmid in vmid_list:
        r = client.find_resource(vmid)
        if not r:
            errors.append(f"VMID {vmid} not found")
            continue
        results.append(
            {
                "vmid": vmid,
                "name": r.get("name", ""),
                "node": r.get("node"),
                "type": r.get("type"),
                "status": r.get("status", ""),
            }
        )
    return results, errors


def confirm_or_dry_run(
    resources: list[dict],
    action: str,
    force: bool,
    dry_run: bool,
) -> bool:
    if dry_run:
        for r in resources:
            s = Text()
            s.append(f"Would {action} ")
            s.append(str(r["vmid"]), style="bold")
            s.append(f" ({r['name']}) - {r['status']}")
            typer.echo(s)
        return False

    if not force:
        typer.echo(f"\nThe following resources will be {action}ed:")
        for r in resources:
            typer.echo(f"  {r['vmid']} ({r['name']}) - {r['status']}")
        typer.echo("")
        typer.confirm("Are you sure you want to proceed?", abort=True)

    return True


ACTION_LABELS: dict[str, str] = {
    "start": "Starting",
    "stop": "Stopping",
    "shutdown": "Shutting down",
    "reboot": "Rebooting",
    "suspend": "Suspending",
    "resume": "Resuming",
}


def execute_action(
    resources: list[dict],
    client: ProxmoxClient,
    action_func: Callable,
    action_name: str,
    wait: bool,
) -> None:
    label = ACTION_LABELS.get(action_name, action_name.capitalize())
    for r in resources:
        typer.echo(f"  {label} {r['vmid']} ({r['name']})... ", nl=False)
        try:
            data = action_func(r["node"], r["type"], r["vmid"])
            upid = data.get("upid")
            if wait and upid:
                typer.echo("waiting... ", nl=False)
                ok = client.wait_for_task(r["node"], upid)
                typer.echo("done" if ok else "failed")
            else:
                typer.echo("done")
        except Exception as e:
            typer.echo(f"failed ({e})")


def print_vm_table(resources: list[dict], color: bool) -> None:
    console = Console(no_color=not color)
    table = Table(
        title="Proxmox Resources",
        title_style=Style(bold=True),
        header_style=(
            Style(color="cyan", bold=True) if color else Style(bold=True)
        ),
        border_style="blue" if color else None,
    )
    table.add_column("VMID", justify="right")
    table.add_column("Name")
    table.add_column("Status")
    table.add_column("Node")
    table.add_column("Pool")
    table.add_column("Type")

    for r in resources:
        status = r.get("status", "")
        row_style = COLOR_STYLES.get(status) if color else None
        table.add_row(
            str(r.get("vmid", "")),
            r.get("name", ""),
            status,
            r.get("node", ""),
            r.get("pool", "") or "-",
            r.get("type", ""),
            style=row_style,
        )
    console.print(table)


def print_node_table(resources: list[dict], color: bool) -> None:
    console = Console(no_color=not color)
    table = Table(
        title="Proxmox Nodes",
        title_style=Style(bold=True),
        header_style=(
            Style(color="cyan", bold=True) if color else Style(bold=True)
        ),
        border_style="blue" if color else None,
    )
    table.add_column("Node")
    table.add_column("Status")
    table.add_column("CPU")
    table.add_column("Memory")
    table.add_column("Disk")

    for r in resources:
        status = r.get("status", "")
        row_style = COLOR_STYLES.get(status) if color else None
        mem_total = r.get("maxmem", 0)
        disk_total = r.get("maxdisk", 0)
        table.add_row(
            r.get("name", r.get("node", "")),
            status,
            f"{r.get('cpu', 0) * 100:.1f}%",
            human_size(mem_total),
            human_size(disk_total),
            style=row_style,
        )
    console.print(table)


def print_storage_table(resources: list[dict], color: bool) -> None:
    console = Console(no_color=not color)
    table = Table(
        title="Proxmox Storage",
        title_style=Style(bold=True),
        header_style=(
            Style(color="cyan", bold=True) if color else Style(bold=True)
        ),
        border_style="blue" if color else None,
    )
    table.add_column("Storage")
    table.add_column("Type")
    table.add_column("Used")
    table.add_column("Available")
    table.add_column("Content")

    for r in resources:
        used = r.get("used", 0)
        avail = r.get("avail", 0)
        total = used + avail
        pct = (used / total * 100) if total else 0
        table.add_row(
            r.get("storage", ""),
            r.get("type", ""),
            f"{human_size(used)} ({pct:.0f}%)",
            human_size(avail),
            r.get("content", ""),
        )
    console.print(table)


def matches(resource: dict, filters: dict) -> bool:
    for key, value in filters.items():
        if value is None:
            continue
        field = resource.get(key, "")
        if field is None:
            field = ""
        if "*" in str(value) or "?" in str(value):
            if not fnmatch.fnmatch(str(field), str(value)):
                return False
        elif str(field).lower() != str(value).lower():
            return False
    return True


def print_json(data: Any, color: bool) -> None:
    if color:
        Console().print_json(data=data)
    else:
        typer.echo(json.dumps(data, indent=2))


def human_size(bytes_val: int | None) -> str:
    if not bytes_val:
        return "0 B"
    val: float = bytes_val
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if abs(val) < 1024:
            return f"{val:.1f} {unit}"
        val /= 1024
    return f"{val:.1f} PiB"


def human_time(seconds: int | None) -> str:
    if not seconds:
        return ""
    days, rem = divmod(int(seconds), 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    parts: list[str] = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)
