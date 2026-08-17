
import time

import typer
from rich.console import Console
from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.text import Text

from ..utils import (
    COLOR_STYLES,
    confirm_or_dry_run,
    execute_action,
    get_client,
    human_size,
    human_time,
    matches,
    print_json,
    print_vm_table,
    print_vm_top_table,
    resolve_vmids,
)
from .snapshot import snapshot_app

vm_app = typer.Typer(
    help="Manage VMs and containers",
    no_args_is_help=True,
)

vm_app.add_typer(
    snapshot_app,
    name="snapshot",
    help="Manage VM/container snapshots",
)


# ── list ──────────────────────────────────────────────────────────────────────

@vm_app.command("list")
def vm_list(
    f_status: str | None = typer.Option(
        None, "--status", help="Filter by status (running, stopped)"
    ),
    f_name: str | None = typer.Option(
        None, "--name", help="Filter by name (supports * and ? wildcards)"
    ),
    f_pool: str | None = typer.Option(
        None, "--pool", help="Filter by pool name"
    ),
    f_node: str | None = typer.Option(
        None, "--node", help="Filter by node name"
    ),
    f_vmid: int | None = typer.Option(
        None, "--vmid", help="Filter by VMID"
    ),
    type_filter: str = typer.Option(
        "all",
        "--type",
        "-t",
        help="Resource type (vm, container, all)",
    ),
    output: str = typer.Option(
        "table", "--output", "-o", help="Output format (table, json)"
    ),
    color: bool = typer.Option(
        False, "--color", "-c", help="Enable colored output"
    ),
):
    """List VMs and containers."""
    client = get_client()

    resources: list[dict] = []
    if type_filter in ("vm", "all"):
        resources.extend(client.list_vms())
    if type_filter in ("container", "all"):
        resources.extend(client.list_containers())

    filter_map = {
        "f_status": "status",
        "f_name": "name",
        "f_pool": "pool",
        "f_node": "node",
        "f_vmid": "vmid",
    }
    resolved = {m: locals().get(k) for k, m in filter_map.items()}
    resources = [r for r in resources if matches(r, resolved)]

    resources.sort(key=lambda r: (r.get("type", ""), r.get("vmid", 0)))

    if output == "json":
        print_json(resources, color)
        return

    print_vm_table(resources, color)


# ── start ─────────────────────────────────────────────────────────────────────

def start(
    vmids: list[int] = typer.Argument(..., help="VM or container IDs to start"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be done without executing"
    ),
    wait: bool = typer.Option(False, "--wait", help="Wait for the action to complete"),
):
    """Start one or more VMs or containers."""
    client = get_client()
    resources, errors = resolve_vmids(vmids, client)
    for e in errors:
        typer.echo(f"Error: {e}", err=True)
    if not resources:
        return

    already_running = [r for r in resources if r["status"] == "running"]
    to_start = [r for r in resources if r["status"] != "running"]
    if already_running:
        for r in already_running:
            typer.echo(f"{r['vmid']} ({r['name']}) already running")
    if not to_start:
        return
    if not confirm_or_dry_run(to_start, "start", force, dry_run):
        return
    execute_action(to_start, client, client.start, "start", wait)


# ── stop ──────────────────────────────────────────────────────────────────────

def stop(
    vmids: list[int] = typer.Argument(..., help="VM or container IDs to stop"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be done without executing"
    ),
    wait: bool = typer.Option(False, "--wait", help="Wait for the action to complete"),
):
    """Stop one or more VMs or containers (force power-off)."""
    client = get_client()
    resources, errors = resolve_vmids(vmids, client)
    for e in errors:
        typer.echo(f"Error: {e}", err=True)
    if not resources:
        return

    already_stopped = [r for r in resources if r["status"] != "running"]
    to_stop = [r for r in resources if r["status"] == "running"]
    if already_stopped:
        for r in already_stopped:
            typer.echo(f"{r['vmid']} ({r['name']}) already stopped")
    if not to_stop:
        return
    if not confirm_or_dry_run(to_stop, "stop", force, dry_run):
        return
    execute_action(to_stop, client, client.stop, "stop", wait)


# ── shutdown ──────────────────────────────────────────────────────────────────

def shutdown(
    vmids: list[int] = typer.Argument(..., help="VM or container IDs to shut down"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be done without executing"
    ),
    wait: bool = typer.Option(False, "--wait", help="Wait for the action to complete"),
):
    """Gracefully shut down one or more VMs or containers."""
    client = get_client()
    resources, errors = resolve_vmids(vmids, client)
    for e in errors:
        typer.echo(f"Error: {e}", err=True)
    if not resources:
        return

    already_stopped = [r for r in resources if r["status"] != "running"]
    to_shutdown = [r for r in resources if r["status"] == "running"]
    if already_stopped:
        for r in already_stopped:
            typer.echo(f"{r['vmid']} ({r['name']}) already stopped")
    if not to_shutdown:
        return
    if not confirm_or_dry_run(to_shutdown, "shutdown", force, dry_run):
        return
    execute_action(to_shutdown, client, client.shutdown, "shutdown", wait)


# ── reboot ────────────────────────────────────────────────────────────────────

def reboot(
    vmids: list[int] = typer.Argument(..., help="VM or container IDs to reboot"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be done without executing"
    ),
    wait: bool = typer.Option(False, "--wait", help="Wait for the action to complete"),
):
    """Reboot one or more VMs or containers."""
    client = get_client()
    resources, errors = resolve_vmids(vmids, client)
    for e in errors:
        typer.echo(f"Error: {e}", err=True)
    if not resources:
        return

    not_running = [r for r in resources if r["status"] != "running"]
    to_reboot = [r for r in resources if r["status"] == "running"]
    if not_running:
        for r in not_running:
            typer.echo(f"{r['vmid']} ({r['name']}) is not running, skipping")
    if not to_reboot:
        return
    if not confirm_or_dry_run(to_reboot, "reboot", force, dry_run):
        return
    execute_action(to_reboot, client, client.reboot, "reboot", wait)


# ── suspend ───────────────────────────────────────────────────────────────────

def suspend(
    vmids: list[int] = typer.Argument(..., help="VM or container IDs to suspend"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be done without executing"
    ),
    wait: bool = typer.Option(False, "--wait", help="Wait for the action to complete"),
):
    """Suspend/pause one or more VMs or containers."""
    client = get_client()
    resources, errors = resolve_vmids(vmids, client)
    for e in errors:
        typer.echo(f"Error: {e}", err=True)
    if not resources:
        return

    not_running = [r for r in resources if r["status"] != "running"]
    to_suspend = [r for r in resources if r["status"] == "running"]
    if not_running:
        for r in not_running:
            typer.echo(f"{r['vmid']} ({r['name']}) is not running, skipping")
    if not to_suspend:
        return
    if not confirm_or_dry_run(to_suspend, "suspend", force, dry_run):
        return
    execute_action(to_suspend, client, client.suspend, "suspend", wait)


# ── resume ────────────────────────────────────────────────────────────────────

def resume(
    vmids: list[int] = typer.Argument(..., help="VM or container IDs to resume"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be done without executing"
    ),
    wait: bool = typer.Option(False, "--wait", help="Wait for the action to complete"),
):
    """Resume one or more suspended VMs or containers."""
    client = get_client()
    resources, errors = resolve_vmids(vmids, client)
    for e in errors:
        typer.echo(f"Error: {e}", err=True)
    if not resources:
        return

    if not confirm_or_dry_run(resources, "resume", force, dry_run):
        return
    execute_action(resources, client, client.resume, "resume", wait)


# ── status ────────────────────────────────────────────────────────────────────

def status(
    vmids: list[int] = typer.Argument(..., help="VM or container IDs to inspect"),
):
    """Show detailed status of one or more VMs or containers."""
    client = get_client()

    for vmid in vmids:
        r = client.find_resource(vmid)
        if not r:
            typer.echo(f"Error: VMID {vmid} not found", err=True)
            continue

        detail = client.get_detail(r["node"], r["type"], vmid)

        mem_total = detail.get("maxmem", r.get("maxmem", 0))
        mem_used = detail.get("mem", r.get("mem", 0))
        disk_total = detail.get("maxdisk", r.get("maxdisk", 0))
        cpu_count = detail.get("cpus", r.get("maxcpu", 0))
        cpu_load = detail.get("cpu", r.get("cpu", 0))
        uptime_sec = detail.get("uptime", r.get("uptime", 0))
        net_in = r.get("netin", 0)
        net_out = r.get("netout", 0)
        disk_read = r.get("diskread", 0)
        disk_write = r.get("diskwrite", 0)
        tags = r.get("tags", "")
        pool = r.get("pool", "-") or "-"

        mem_pct = (mem_used / mem_total * 100) if mem_total else 0
        cpu_pct = cpu_load * 100

        lines: list[str] = []
        lines.append(f"VMID:     {vmid}")
        lines.append(f"Name:     {r.get('name', '')}")
        lines.append(f"Status:   {r.get('status', '')}")
        lines.append(f"Node:     {r.get('node', '')}")
        lines.append(f"Type:     {r.get('type', '')}")
        lines.append(f"Pool:     {pool}")
        if tags:
            lines.append(f"Tags:     {tags}")
        lines.append("")
        lines.append(
            f"CPU:      {cpu_count} core(s) ({cpu_pct:.1f}%)"
        )
        lines.append(
            f"Memory:   {human_size(mem_used)} / {human_size(mem_total)} "
            f"({mem_pct:.0f}%)"
        )
        lines.append(f"Disk:     {human_size(disk_total)}")
        if uptime_sec:
            lines.append(f"Uptime:   {human_time(uptime_sec)}")
        if net_in or net_out:
            lines.append(
                f"Network:  {human_size(net_in)} in / {human_size(net_out)} out"
            )
        if disk_read or disk_write:
            lines.append(
                f"I/O:      {human_size(disk_read)} read / "
                f"{human_size(disk_write)} written"
            )

        console = Console()
        status_style = COLOR_STYLES.get(r.get("status", ""), Style())
        panel = Panel(
            "\n".join(lines),
            title=Text(f" {r.get('name', '')} ", style=status_style),
            border_style="blue" if console.color_system else None,  # type: ignore[arg-type]
        )
        console.print(panel)

        if len(vmids) > 1:
            typer.echo("")


# ── info ──────────────────────────────────────────────────────────────────────

CONFIG_BASIC_KEYS = {
    "vmid",
    "name",
    "status",
    "node",
    "type",
    "cores",
    "sockets",
    "memory",
    "ostype",
    "boot",
    "bootdisk",
    "tags",
}


def config_rows(config: dict) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = [
        ("VMID", str(config.get("vmid", ""))),
        ("Name", str(config.get("name", ""))),
        ("Status", str(config.get("status", ""))),
        ("Node", str(config.get("node", ""))),
        ("Type", str(config.get("type", ""))),
    ]
    cores = config.get("cores")
    sockets = config.get("sockets")
    if cores or sockets:
        rows.append(("vCPUs", str(int(cores or 1) * int(sockets or 1))))
    if config.get("memory"):
        memory_bytes = int(config["memory"]) * 1024 * 1024
        rows.append(("Memory", human_size(memory_bytes)))
    if config.get("ostype"):
        rows.append(("OS Type", str(config["ostype"])))
    if config.get("boot"):
        rows.append(("Boot", str(config["boot"])))
    if config.get("bootdisk"):
        rows.append(("Boot Disk", str(config["bootdisk"])))
    if config.get("tags"):
        rows.append(("Tags", str(config["tags"])))
    for key in sorted(set(config) - CONFIG_BASIC_KEYS):
        rows.append((key, str(config[key])))
    return rows


def info(
    vmid: int = typer.Argument(..., help="VM or container ID"),
    output: str = typer.Option(
        "table", "--output", "-o", help="Output format (table, json)"
    ),
    color: bool = typer.Option(
        False, "--color", "-c", help="Enable colored output"
    ),
):
    """Show basic configuration of a VM or container."""
    client = get_client()
    r = client.find_resource(vmid)
    if not r:
        typer.echo(f"Error: VMID {vmid} not found", err=True)
        raise typer.Exit(1)

    config = client.get_config(r["node"], r["type"], vmid)
    config["vmid"] = vmid
    config.setdefault("name", r.get("name", ""))
    config.setdefault("status", r.get("status", ""))
    config.setdefault("node", r.get("node", ""))
    config.setdefault("type", r.get("type", ""))

    if output == "json":
        print_json(config, color)
        return

    console = Console(no_color=not color)
    table = Table(
        title=f"Configuration of {vmid} ({config.get('name', '')})",
        title_style=Style(bold=True),
        header_style=(
            Style(color="cyan", bold=True) if color else Style(bold=True)
        ),
        border_style="blue" if color else None,
        show_header=False,
    )
    table.add_column("Property", style="bold")
    table.add_column("Value")

    for prop, value in config_rows(config):
        table.add_row(prop, value)
    console.print(table)


# ── top ───────────────────────────────────────────────────────────────────────


def top(
    vmids: list[int] | None = typer.Argument(
        None, help="VM or container IDs to monitor (all if omitted)"
    ),
    watch: bool = typer.Option(
        False, "--watch", "-w", help="Live-refreshing display"
    ),
    interval: int = typer.Option(
        5, "--interval", "-i", help="Refresh interval in seconds (with --watch)"
    ),
    output: str = typer.Option(
        "table", "--output", "-o", help="Output format (table, json)"
    ),
    color: bool = typer.Option(
        False, "--color", "-c", help="Enable colored output"
    ),
    f_node: str | None = typer.Option(
        None, "--node", help="Filter by node name"
    ),
):
    """Show resource usage for VMs and containers."""
    client = get_client()

    def fetch_metrics() -> list[dict]:
        resources = client.list_resources("vm")
        if f_node:
            resources = [r for r in resources if r.get("node") == f_node]
        if vmids:
            vmid_set = set(vmids)
            resources = [r for r in resources if r.get("vmid") in vmid_set]
        resources.sort(key=lambda r: r.get("cpu", 0), reverse=True)
        return resources

    if watch:
        try:
            while True:
                resources = fetch_metrics()
                if output == "json":
                    print_json(resources, color)
                else:
                    print_vm_top_table(resources, color)
                time.sleep(interval)
        except KeyboardInterrupt:
            raise typer.Exit()
    else:
        resources = fetch_metrics()
        if output == "json":
            print_json(resources, color)
        else:
            print_vm_top_table(resources, color)


# ── Register commands on vm_app ──────────────────────────────────────────────

vm_app.command(name="start")(start)
vm_app.command(name="stop")(stop)
vm_app.command(name="shutdown")(shutdown)
vm_app.command(name="reboot")(reboot)
vm_app.command(name="suspend")(suspend)
vm_app.command(name="resume")(resume)
vm_app.command(name="status")(status)
vm_app.command(name="info")(info)
vm_app.command(name="top")(top)
