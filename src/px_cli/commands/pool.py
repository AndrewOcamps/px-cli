
import typer
from rich.console import Console
from rich.style import Style
from rich.table import Table

from ..utils import get_client, print_json

pool_app = typer.Typer(
    help="Manage resource pools",
    no_args_is_help=True,
)


@pool_app.command("list")
def pool_list(
    output: str = typer.Option(
        "table", "--output", "-o", help="Output format (table, json)"
    ),
    color: bool = typer.Option(False, "--color", "-c", help="Enable colored output"),
):
    """List resource pools."""
    client = get_client()
    pools = client.list_pools()

    if output == "json":
        print_json(pools, color)
        return

    console = Console(no_color=not color)
    table = Table(
        title="Resource Pools",
        title_style=Style(bold=True),
        header_style=(
            Style(color="cyan", bold=True) if color else Style(bold=True)
        ),
        border_style="blue" if color else None,
    )
    table.add_column("Pool ID")
    table.add_column("Comment")
    table.add_column("Members")

    for p in pools:
        members = p.get("members", [])
        member_count = len(members) if members else 0
        table.add_row(
            p.get("poolid", ""),
            p.get("comment", "") or "-",
            str(member_count),
        )

    console.print(table)


@pool_app.command("create")
def pool_create(
    name: str = typer.Argument(..., help="Pool name"),
    comment: str | None = typer.Option(None, "--comment", "-c", help="Pool description"),
):
    """Create a new resource pool."""
    client = get_client()
    typer.echo(f"Creating pool '{name}'... ", nl=False)
    try:
        client.create_pool(name, comment=comment or "")
        typer.echo("done")
    except Exception as e:
        typer.echo(f"failed ({e})")
        raise typer.Exit(1)


@pool_app.command("delete")
def pool_delete(
    name: str = typer.Argument(..., help="Pool name to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete a resource pool."""
    if not force:
        typer.confirm(f"Delete pool '{name}'?", abort=True)

    client = get_client()
    typer.echo(f"Deleting pool '{name}'... ", nl=False)
    try:
        client.delete_pool(name)
        typer.echo("done")
    except Exception as e:
        typer.echo(f"failed ({e})")
        raise typer.Exit(1)


@pool_app.command("show")
def pool_show(
    name: str = typer.Argument(..., help="Pool name"),
    color: bool = typer.Option(False, "--color", "-c", help="Enable colored output"),
):
    """Show pool details and members."""
    client = get_client()
    try:
        pool = client.get_pool(name)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    console = Console(no_color=not color)
    from rich.panel import Panel
    from rich.text import Text

    members = pool.get("members", [])
    lines: list[str] = [
        f"Pool ID:  {pool.get('poolid', '')}",
        f"Comment:  {pool.get('comment', '-')}",
        f"Members:  {len(members)}",
    ]
    if members:
        lines.append("")
        lines.append("Resources:")
        for m in members:
            lines.append(
                f"  {m.get('vmid', '')} ({m.get('name', '')}) - "
                f"{m.get('type', '')} - {m.get('node', '')} - {m.get('status', '')}"
            )

    panel = Panel(
        "\n".join(lines),
        title=Text(f" Pool: {name} ", style=Style(bold=True)),
        border_style="blue" if console.color_system else None,  # type: ignore[arg-type]
    )
    console.print(panel)


@pool_app.command("add")
def pool_add(
    name: str = typer.Argument(..., help="Pool name"),
    vmids: list[int] = typer.Argument(..., help="VM or container IDs to add"),
):
    """Add VMs/containers to a pool."""
    client = get_client()

    for vmid in vmids:
        typer.echo(f"Adding VMID {vmid} to pool '{name}'... ", nl=False)
        try:
            client.update_pool(name, {"vmid": vmid})
            typer.echo("done")
        except Exception as e:
            typer.echo(f"failed ({e})")


@pool_app.command("remove")
def pool_remove(
    name: str = typer.Argument(..., help="Pool name"),
    vmids: list[int] = typer.Argument(..., help="VM or container IDs to remove"),
):
    """Remove VMs/containers from a pool."""
    client = get_client()

    for vmid in vmids:
        typer.echo(f"Removing VMID {vmid} from pool '{name}'... ", nl=False)
        try:
            client.update_pool(name, {"vmid": vmid, "delete": 1})
            typer.echo("done")
        except Exception as e:
            typer.echo(f"failed ({e})")
