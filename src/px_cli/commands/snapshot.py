
import typer
from rich.console import Console
from rich.style import Style
from rich.table import Table

from ..utils import get_client

snapshot_app = typer.Typer(
    help="Manage VM/container snapshots",
    no_args_is_help=True,
)


@snapshot_app.command("list")
def snapshot_list(
    vmid: int = typer.Argument(..., help="VM or container ID"),
):
    """List snapshots for a VM or container."""
    client = get_client()
    r = client.find_resource(vmid)
    if not r:
        typer.echo(f"Error: VMID {vmid} not found", err=True)
        raise typer.Exit(1)

    snapshots = client.list_snapshots(r["node"], r["type"], vmid)
    current_snap = r.get("snapshots", "")
    current_list = current_snap.split(";") if current_snap else []

    table = Table(
        title=f"Snapshots for {vmid} ({r.get('name', '')})",
        title_style=Style(bold=True),
        header_style=Style(color="cyan", bold=True),
        border_style="blue",
    )
    table.add_column("Name")
    table.add_column("Description")
    table.add_column("Date")
    table.add_column("VM State")
    table.add_column("Parent")
    table.add_column("Current")

    for snap in snapshots:
        snapname = snap.get("name", "")
        if snapname == "current":
            continue
        snaptime = snap.get("snaptime", 0)
        import datetime
        date_str = (
            datetime.datetime.fromtimestamp(snaptime / 1000000).strftime("%Y-%m-%d %H:%M")
            if snaptime
            else ""
        )
        table.add_row(
            snapname,
            snap.get("description", "") or "-",
            date_str,
            "yes" if snap.get("vmstate") else "no",
            snap.get("parent", "-"),
            "yes" if snapname in current_list else "",
        )

    console = Console()
    console.print(table)


@snapshot_app.command("create")
def snapshot_create(
    vmid: int = typer.Argument(..., help="VM or container ID"),
    name: str = typer.Argument(..., help="Snapshot name"),
    description: str | None = typer.Option(
        None, "--description", "-d", help="Snapshot description"
    ),
    vmstate: bool = typer.Option(False, "--vmstate", help="Include RAM state"),
    wait: bool = typer.Option(False, "--wait", help="Wait for the task to complete"),
):
    """Create a snapshot of a VM or container."""
    client = get_client()
    r = client.find_resource(vmid)
    if not r:
        typer.echo(f"Error: VMID {vmid} not found", err=True)
        raise typer.Exit(1)

    typer.echo(f"Creating snapshot '{name}' for {vmid} ({r.get('name', '')})... ", nl=False)
    try:
        data = client.create_snapshot(
            r["node"], r["type"], vmid, name,
            description=description or "",
            vmstate=vmstate,
        )
        upid = data.get("upid")
        if wait and upid:
            typer.echo("waiting... ", nl=False)
            ok = client.wait_for_task(r["node"], upid)
            typer.echo("done" if ok else "failed")
        else:
            typer.echo("done")
    except Exception as e:
        typer.echo(f"failed ({e})")
        raise typer.Exit(1)


@snapshot_app.command("delete")
def snapshot_delete(
    vmid: int = typer.Argument(..., help="VM or container ID"),
    name: str = typer.Argument(..., help="Snapshot name"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
    wait: bool = typer.Option(False, "--wait", help="Wait for the task to complete"),
):
    """Delete a snapshot from a VM or container."""
    if not force:
        typer.confirm(
            f"Delete snapshot '{name}' from VMID {vmid}?",
            abort=True,
        )

    client = get_client()
    r = client.find_resource(vmid)
    if not r:
        typer.echo(f"Error: VMID {vmid} not found", err=True)
        raise typer.Exit(1)

    typer.echo(f"Deleting snapshot '{name}' from {vmid}... ", nl=False)
    try:
        data = client.delete_snapshot(r["node"], r["type"], vmid, name)
        upid = data.get("upid")
        if wait and upid:
            typer.echo("waiting... ", nl=False)
            ok = client.wait_for_task(r["node"], upid)
            typer.echo("done" if ok else "failed")
        else:
            typer.echo("done")
    except Exception as e:
        typer.echo(f"failed ({e})")
        raise typer.Exit(1)


@snapshot_app.command("rollback")
def snapshot_rollback(
    vmid: int = typer.Argument(..., help="VM or container ID"),
    name: str = typer.Argument(..., help="Snapshot name to rollback to"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
    wait: bool = typer.Option(False, "--wait", help="Wait for the task to complete"),
):
    """Rollback a VM or container to a snapshot."""
    if not force:
        typer.confirm(
            f"Rollback VMID {vmid} to snapshot '{name}'? "
            "This will revert all changes since the snapshot.",
            abort=True,
        )

    client = get_client()
    r = client.find_resource(vmid)
    if not r:
        typer.echo(f"Error: VMID {vmid} not found", err=True)
        raise typer.Exit(1)

    typer.echo(f"Rolling back {vmid} to snapshot '{name}'... ", nl=False)
    try:
        data = client.rollback_snapshot(r["node"], r["type"], vmid, name)
        upid = data.get("upid")
        if wait and upid:
            typer.echo("waiting... ", nl=False)
            ok = client.wait_for_task(r["node"], upid)
            typer.echo("done" if ok else "failed")
        else:
            typer.echo("done")
    except Exception as e:
        typer.echo(f"failed ({e})")
        raise typer.Exit(1)
