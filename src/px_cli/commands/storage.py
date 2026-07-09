
import typer
from rich.console import Console
from rich.style import Style
from rich.table import Table

from ..utils import get_client, human_size, print_json

storage_app = typer.Typer(
    help="Manage storage pools and contents",
    no_args_is_help=True,
)


@storage_app.command("list")
def storage_list(
    output: str = typer.Option(
        "table", "--output", "-o", help="Output format (table, json)"
    ),
    color: bool = typer.Option(False, "--color", "-c", help="Enable colored output"),
):
    """List storage pools."""
    client = get_client()
    storages = client.list_storages()

    if output == "json":
        print_json(storages, color)
        return

    console = Console(no_color=not color)
    table = Table(
        title="Storage Pools",
        title_style=Style(bold=True),
        header_style=(
            Style(color="cyan", bold=True) if color else Style(bold=True)
        ),
        border_style="blue" if color else None,
    )
    table.add_column("Storage")
    table.add_column("Type")
    table.add_column("Content")
    table.add_column("Used")
    table.add_column("Available")
    table.add_column("Total")

    for s in storages:
        used = s.get("used", 0)
        avail = s.get("avail", 0)
        total = s.get("total", used + avail)
        pct = (used / total * 100) if total else 0
        table.add_row(
            s.get("storage", ""),
            s.get("type", ""),
            s.get("content", ""),
            f"{human_size(used)} ({pct:.0f}%)",
            human_size(avail),
            human_size(total),
        )

    console.print(table)


@storage_app.command("content")
def storage_content(
    storage: str = typer.Argument(..., help="Storage pool ID"),
    node: str | None = typer.Option(None, "--node", "-n", help="Node name"),
    content_type: str | None = typer.Option(
        None, "--type", "-t", help="Content type (iso, vztmpl, backup, rootdir, images)"
    ),
    output: str = typer.Option(
        "table", "--output", "-o", help="Output format (table, json)"
    ),
    color: bool = typer.Option(False, "--color", "-c", help="Enable colored output"),
):
    """List contents of a storage pool."""
    client = get_client()

    if not node:
        resources = client.list_resources("node")
        if not resources:
            typer.echo("Error: No nodes found", err=True)
            raise typer.Exit(1)
        node = resources[0]["node"]

    try:
        contents = client.storage_content(storage, node)
    except Exception as e:
        typer.echo(f"Error accessing storage: {e}", err=True)
        raise typer.Exit(1)

    if content_type:
        contents = [c for c in contents if c.get("content") == content_type]

    if output == "json":
        print_json(contents, color)
        return

    console = Console(no_color=not color)
    table = Table(
        title=f"Storage: {storage} (node: {node})",
        title_style=Style(bold=True),
        header_style=(
            Style(color="cyan", bold=True) if color else Style(bold=True)
        ),
        border_style="blue" if color else None,
    )
    table.add_column("Volume ID")
    table.add_column("Type")
    table.add_column("Format")
    table.add_column("Size")

    for c in contents:
        volid = c.get("volid", "")
        if "/" in volid:
            volid = volid.split("/", 1)[1] if "/" in volid else volid
        table.add_row(
            volid,
            c.get("content", ""),
            c.get("format", ""),
            human_size(c.get("size", 0)),
        )

    console.print(table)


@storage_app.command("info")
def storage_info(
    storage: str = typer.Argument(..., help="Storage pool ID"),
    color: bool = typer.Option(False, "--color", "-c", help="Enable colored output"),
):
    """Show detailed info about a storage pool."""
    client = get_client()
    storages = client.list_storages()
    s = next((s for s in storages if s.get("storage") == storage), None)
    if not s:
        typer.echo(f"Error: Storage '{storage}' not found", err=True)
        raise typer.Exit(1)

    console = Console(no_color=not color)
    from rich.panel import Panel
    from rich.text import Text

    used = s.get("used", 0)
    avail = s.get("avail", 0)
    total = s.get("total", used + avail)
    pct = (used / total * 100) if total else 0

    lines = [
        f"Storage:  {s.get('storage', '')}",
        f"Type:     {s.get('type', '')}",
        f"Content:  {s.get('content', '')}",
        f"Node:     {s.get('node', '')}",
        f"Path:     {s.get('path', '')}",
        "",
        f"Used:     {human_size(used)} ({pct:.0f}%)",
        f"Free:     {human_size(avail)}",
        f"Total:    {human_size(total)}",
    ]

    panel = Panel(
        "\n".join(lines),
        title=Text(f"Storage: {storage}", style=Style(bold=True)),
        border_style="blue" if console.color_system else None,  # type: ignore[arg-type]
    )
    console.print(panel)
