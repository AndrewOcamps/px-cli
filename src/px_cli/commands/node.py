
import typer
from rich.console import Console
from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.text import Text

from ..utils import (
    COLOR_STYLES,
    get_client,
    human_size,
    human_time,
    print_json,
)

node_app = typer.Typer(
    help="Manage Proxmox nodes",
    no_args_is_help=True,
)


@node_app.command("list")
def node_list(
    output: str = typer.Option(
        "table", "--output", "-o", help="Output format (table, json)"
    ),
    color: bool = typer.Option(False, "--color", "-c", help="Enable colored output"),
):
    """List nodes in the cluster."""
    client = get_client()
    resources = client.list_resources("node")

    if output == "json":
        print_json(resources, color)
        return

    console = Console(no_color=not color)
    table = Table(
        title="Cluster Nodes",
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
        cpu_load = r.get("cpu", 0)
        mem_used = r.get("mem", 0)
        mem_total = r.get("maxmem", 0)
        mem_pct = (mem_used / mem_total * 100) if mem_total else 0
        disk_total = r.get("maxdisk", 0)

        table.add_row(
            r.get("name", r.get("node", "")),
            status,
            f"{cpu_load * 100:.1f}%",
            f"{human_size(mem_used)} / {human_size(mem_total)} ({mem_pct:.0f}%)",
            human_size(disk_total),
            style=row_style,
        )

    console.print(table)


@node_app.command("status")
def node_status(
    node: str = typer.Argument(..., help="Node name"),
    color: bool = typer.Option(False, "--color", "-c", help="Enable colored output"),
):
    """Show detailed node status."""
    client = get_client()
    try:
        status = client.get_node_status(node)
    except Exception as e:
        typer.echo(f"Error getting node status: {e}", err=True)
        raise typer.Exit(1)

    console = Console(no_color=not color)
    lines: list[str] = [
        f"Node:     {status.get('node', node)}",
        f"Status:   {status.get('status', '')}",
        f"Version:  {status.get('version', '')}",
        f"CPUs:     {status.get('cpus', status.get('maxcpu', 0))}",
        f"CPU Freq: {status.get('cpu_frequency', '')}",
        f"CPU Load: {status.get('cpu', 0) * 100:.1f}%",
        f"Memory:   {human_size(status.get('mem', 0))} / {human_size(status.get('maxmem', 0))}",
        f"Disk:     {human_size(status.get('disk', 0))} / {human_size(status.get('maxdisk', 0))}",
        f"SWAP:     {human_size(status.get('swap', 0))} / {human_size(status.get('maxswap', 0))}",
        f"Uptime:   {human_time(status.get('uptime', 0))}",
        f"KSM:      {status.get('ksm', '')}",
        f"Load Avg: {status.get('loadavg', [''])[:3]}",
    ]

    panel = Panel(
        "\n".join(lines),
        title=Text(f" Node: {node} ", style=Style(bold=True)),
        border_style="blue" if console.color_system else None,  # type: ignore[arg-type]
    )
    console.print(panel)


@node_app.command("info")
def node_info(
    node: str = typer.Argument(..., help="Node name"),
    color: bool = typer.Option(False, "--color", "-c", help="Enable colored output"),
):
    """Show node version and system information."""
    client = get_client()
    console = Console(no_color=not color)

    try:
        version = client.get_node_version(node)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    lines: list[str] = [
        f"Node:       {node}",
        f"Release:    {version.get('release', '')}",
        f"Version:    {version.get('version', '')}",
        f"Repository: {version.get('repoid', '')}",
        f"Kernel:     {version.get('kernel', '')}",
        f"PVE:        {version.get('pve', '')}",
        f"QEMU:       {version.get('qemu', '')}",
        f"LXC:        {version.get('lxc', '')}",
        f"Proxmox:    {version.get('proxmox', '')}",
    ]

    panel = Panel(
        "\n".join(lines),
        title=Text(f" System Info: {node} ", style=Style(bold=True)),
        border_style="blue" if console.color_system else None,  # type: ignore[arg-type]
    )
    console.print(panel)


@node_app.command("services")
def node_services(
    node: str = typer.Argument(..., help="Node name"),
    output: str = typer.Option(
        "table", "--output", "-o", help="Output format (table, json)"
    ),
    color: bool = typer.Option(False, "--color", "-c", help="Enable colored output"),
):
    """List services running on a node."""
    client = get_client()
    try:
        services = client.list_node_services(node)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    if output == "json":
        print_json(services, color)
        return

    console = Console(no_color=not color)
    table = Table(
        title=f"Services (node: {node})",
        title_style=Style(bold=True),
        header_style=(
            Style(color="cyan", bold=True) if color else Style(bold=True)
        ),
        border_style="blue" if color else None,
    )
    table.add_column("Service")
    table.add_column("State")
    table.add_column("Description")

    for svc in services:
        state = svc.get("state", "")
        row_style = (
            Style(color="green", bold=True)
            if state == "running" and color
            else (
                Style(color="red", bold=True)
                if state == "stopped" and color
                else None
            )
        )
        table.add_row(
            svc.get("name", svc.get("id", "")),
            state,
            svc.get("desc", ""),
            style=row_style,
        )

    console.print(table)


@node_app.command("reboot")
def node_reboot(
    node: str = typer.Argument(..., help="Node name to reboot"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Reboot a node. Requires confirmation unless --force."""
    if not force:
        typer.echo(f"WARNING: This will reboot node '{node}'!")
        typer.confirm("Are you sure?", abort=True)

    client = get_client()
    typer.echo(f"Rebooting node {node}... ", nl=False)
    try:
        client.reboot_node(node)
        typer.echo("done")
    except Exception as e:
        typer.echo(f"failed ({e})")
        raise typer.Exit(1)
