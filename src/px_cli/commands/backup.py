
import typer
from rich.console import Console
from rich.style import Style
from rich.table import Table

from ..utils import get_client, human_size, print_json

backup_app = typer.Typer(
    help="Manage VM/container backups",
    no_args_is_help=True,
)


@backup_app.command("create")
def backup_create(
    vmids: list[int] = typer.Argument(..., help="VM or container IDs to back up"),
    storage: str = typer.Option("local", "--storage", "-s", help="Target storage"),
    mode: str = typer.Option(
        "snapshot", "--mode", "-m", help="Backup mode (snapshot, stop, suspend)"
    ),
    compress: str = typer.Option(
        "zstd", "--compress", help="Compression algorithm (zstd, gzip, lzo, none)"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
    wait: bool = typer.Option(False, "--wait", help="Wait for the backup to complete"),
):
    """Create on-demand backups of VMs or containers (vzdump)."""
    if not force:
        typer.echo(f"\nThe following VMIDs will be backed up to {storage}:")
        for vmid in vmids:
            typer.echo(f"  {vmid}")
        typer.echo("")
        typer.confirm("Are you sure you want to proceed?", abort=True)

    client = get_client()

    for vmid in vmids:
        r = client.find_resource(vmid)
        if not r:
            typer.echo(f"Error: VMID {vmid} not found", err=True)
            continue

        typer.echo(f"Backing up {vmid} ({r.get('name', '')})... ", nl=False)
        try:
            data = client.create_backup(
                r["node"], vmid, storage=storage, mode=mode, compress=compress
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


@backup_app.command("list")
def backup_list(
    storage: str | None = typer.Option(
        None, "--storage", "-s", help="Storage pool to list backups from"
    ),
    node: str | None = typer.Option(None, "--node", "-n", help="Node name"),
    output: str = typer.Option(
        "table", "--output", "-o", help="Output format (table, json)"
    ),
    color: bool = typer.Option(False, "--color", "-c", help="Enable colored output"),
):
    """List available backups."""
    client = get_client()

    if not node:
        resources = client.list_resources("node")
        if not resources:
            typer.echo("Error: No nodes found", err=True)
            raise typer.Exit(1)
        node = resources[0]["node"]

    storages_to_check = [storage] if storage else [
        s["storage"] for s in client.list_storages()
    ]

    all_backups: list[dict] = []
    for st in storages_to_check:
        try:
            contents = client.storage_content(st, node)
            backups = [c for c in contents if c.get("content") == "backup"]
            for b in backups:
                b["_storage"] = st
            all_backups.extend(backups)
        except Exception:
            pass

    if output == "json":
        print_json(all_backups, color)
        return

    console = Console(no_color=not color)
    table = Table(
        title="Backups",
        title_style=Style(bold=True),
        header_style=(
            Style(color="cyan", bold=True) if color else Style(bold=True)
        ),
        border_style="blue" if color else None,
    )
    table.add_column("Storage")
    table.add_column("Volume")
    table.add_column("VMID")
    table.add_column("Size")
    table.add_column("Date")

    for b in all_backups:
        volid = b.get("volid", "")
        short_name = volid.split("/", 1)[1] if "/" in volid else volid
        ctime = b.get("ctime", 0)
        import datetime
        date_str = (
            datetime.datetime.fromtimestamp(ctime).strftime("%Y-%m-%d %H:%M")
            if ctime
            else ""
        )
        table.add_row(
            b.get("_storage", ""),
            short_name,
            b.get("vmid", ""),
            human_size(b.get("size", 0)),
            date_str,
        )

    console.print(table)


@backup_app.command("restore")
def backup_restore(
    vmid: int = typer.Argument(..., help="Target VM or container ID"),
    backup_file: str = typer.Argument(
        ..., help="Backup volume name (e.g. vzdump-qemu-100-2024-01-01.vma.zst)"
    ),
    storage: str = typer.Option(None, "--storage", "-s", help="Storage pool containing the backup"),
    node: str | None = typer.Option(None, "--node", "-n", help="Node to restore to"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
    wait: bool = typer.Option(False, "--wait", help="Wait for the restore to complete"),
):
    """Restore a VM or container from a backup."""
    client = get_client()

    if not node:
        resources = client.list_resources("node")
        if not resources:
            typer.echo("Error: No nodes found", err=True)
            raise typer.Exit(1)
        node = resources[0]["node"]

    if not storage:
        storages = client.list_storages()
        for s in storages:
            try:
                contents = client.storage_content(s["storage"], node)
                for c in contents:
                    if backup_file in c.get("volid", ""):
                        storage = s["storage"]
                        break
            except Exception:
                pass

    if not storage:
        typer.echo("Error: Could not determine storage. Use --storage", err=True)
        raise typer.Exit(1)

    if not force:
        typer.confirm(
            f"Restore VMID {vmid} from {backup_file} on storage {storage}?",
            abort=True,
        )

    full_path = f"{storage}:backup/{backup_file}"
    typer.echo(f"Restoring {vmid} from {full_path}... ", nl=False)
    try:
        data = client.raw_post(
            f"/api2/json/nodes/{node}/vzdump",
            data={"restore": 1, "vmid": vmid, "archive": full_path, "storage": storage},
        )
        upid = data.get("upid")
        if wait and upid:
            typer.echo("waiting... ", nl=False)
            ok = client.wait_for_task(node, upid)
            typer.echo("done" if ok else "failed")
        else:
            typer.echo("done")
    except Exception as e:
        typer.echo(f"failed ({e})")
        raise typer.Exit(1)


@backup_app.command("delete")
def backup_delete(
    vmid: int = typer.Argument(..., help="VMID to remove backups for"),
    keep: str | None = typer.Option(None, "--keep", "-k", help="Volume name pattern to keep"),
    storage: str = typer.Option("local", "--storage", "-s", help="Storage pool"),
    node: str | None = typer.Option(None, "--node", "-n", help="Node name"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete backups for a VM or container."""
    client = get_client()

    if not node:
        resources = client.list_resources("node")
        if not resources:
            typer.echo("Error: No nodes found", err=True)
            raise typer.Exit(1)
        node = resources[0]["node"]

    contents = client.storage_content(storage, node)
    backups = [
        c for c in contents
        if c.get("content") == "backup" and str(c.get("vmid", "")) == str(vmid)
    ]

    if keep:
        backups = [b for b in backups if keep not in b.get("volid", "")]

    if not backups:
        typer.echo(f"No backups found for VMID {vmid}")
        return

    if not force:
        typer.echo(f"\nThe following backups for VMID {vmid} will be deleted:")
        for b in backups:
            volid = b.get("volid", "")
            short = volid.split("/", 1)[1] if "/" in volid else volid
            typer.echo(f"  {short}")
        typer.echo("")
        typer.confirm("Are you sure?", abort=True)

    for b in backups:
        volid = b.get("volid", "")
        short = volid.split("/", 1)[1] if "/" in volid else volid
        typer.echo(f"Deleting {short}... ", nl=False)
        try:
            client.raw_delete(
                f"/api2/json/nodes/{node}/storage/{storage}/content/{volid}"
            )
            typer.echo("done")
        except Exception as e:
            typer.echo(f"failed ({e})")
