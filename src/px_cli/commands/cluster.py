
import typer
from rich.console import Console
from rich.style import Style
from rich.table import Table

from ..utils import COLOR_STYLES, get_client, print_json

cluster_app = typer.Typer(
    help="Cluster information",
    no_args_is_help=True,
)


@cluster_app.command("status")
def cluster_status(
    output: str = typer.Option(
        "table", "--output", "-o", help="Output format (table, json)"
    ),
    color: bool = typer.Option(False, "--color", "-c", help="Enable colored output"),
):
    """Show cluster status."""
    client = get_client()
    try:
        status = client.cluster_status()
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    if output == "json":
        print_json(status, color)
        return

    console = Console(no_color=not color)
    table = Table(
        title="Cluster Status",
        title_style=Style(bold=True),
        header_style=(
            Style(color="cyan", bold=True) if color else Style(bold=True)
        ),
        border_style="blue" if color else None,
    )
    table.add_column("Name")
    table.add_column("Type")
    table.add_column("Status")
    table.add_column("IP")
    table.add_column("Quorate")

    for item in status:
        item_type = item.get("type", "")
        name = item.get("name", item.get("node", ""))
        if item_type == "cluster":
            quorate = "yes" if item.get("quorate") else "no"
            table.add_row(
                name,
                "cluster",
                item.get("status", ""),
                "",
                quorate,
                style=Style(bold=True, color="cyan") if color else Style(bold=True),
            )
        elif item_type == "node":
            row_style = COLOR_STYLES.get(item.get("status", "")) if color else None
            table.add_row(
                name,
                "node",
                item.get("status", ""),
                item.get("ip", ""),
                "",
                style=row_style,
            )

    console.print(table)


@cluster_app.command("resources")
def cluster_resources(
    type_filter: str | None = typer.Option(
        None, "--type", "-t", help="Resource type filter (vm, node, storage)"
    ),
    output: str = typer.Option(
        "table", "--output", "-o", help="Output format (table, json)"
    ),
    color: bool = typer.Option(False, "--color", "-c", help="Enable colored output"),
):
    """List all cluster resources."""
    client = get_client()
    resources = client.list_resources(type_filter)

    if output == "json":
        print_json(resources, color)
        return

    console = Console(no_color=not color)
    table = Table(
        title="Cluster Resources",
        title_style=Style(bold=True),
        header_style=(
            Style(color="cyan", bold=True) if color else Style(bold=True)
        ),
        border_style="blue" if color else None,
    )
    table.add_column("ID")
    table.add_column("Type")
    table.add_column("Node")
    table.add_column("Status")

    for r in resources:
        row_style = COLOR_STYLES.get(r.get("status", "")) if color else None
        table.add_row(
            r.get("id", str(r.get("vmid", ""))),
            r.get("type", ""),
            r.get("node", ""),
            r.get("status", ""),
            style=row_style,
        )

    console.print(table)


@cluster_app.command("log")
def cluster_log(
    max_items: int = typer.Option(50, "--max", "-n", help="Maximum log entries"),
    color: bool = typer.Option(False, "--color", "-c", help="Enable colored output"),
):
    """Show cluster log."""
    client = get_client()
    try:
        entries = client.cluster_log(max_items)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    console = Console(no_color=not color)
    table = Table(
        title="Cluster Log",
        title_style=Style(bold=True),
        header_style=(
            Style(color="cyan", bold=True) if color else Style(bold=True)
        ),
        border_style="blue" if color else None,
    )
    table.add_column("Time")
    table.add_column("Node")
    table.add_column("User")
    table.add_column("Message")

    for entry in entries:
        import datetime
        ts = entry.get("time", 0)
        time_str = (
            datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
            if ts
            else ""
        )
        table.add_row(
            time_str,
            entry.get("node", ""),
            entry.get("user", ""),
            entry.get("msg", ""),
        )

    console.print(table)


@cluster_app.command("next-id")
def cluster_next_id():
    """Get the next available VMID."""
    client = get_client()
    try:
        next_id = client.cluster_next_id()
        typer.echo(next_id)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
