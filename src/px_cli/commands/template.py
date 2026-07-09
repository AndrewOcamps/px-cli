
import typer
from rich.console import Console
from rich.style import Style
from rich.table import Table

from ..utils import get_client, print_json

template_app = typer.Typer(
    help="Manage LXC templates",
    no_args_is_help=True,
)


@template_app.command("list")
def template_list(
    node: str | None = typer.Option(None, "--node", "-n", help="Node name"),
    output: str = typer.Option(
        "table", "--output", "-o", help="Output format (table, json)"
    ),
    color: bool = typer.Option(False, "--color", "-c", help="Enable colored output"),
):
    """List available LXC templates."""
    client = get_client()

    if not node:
        resources = client.list_resources("node")
        if not resources:
            typer.echo("Error: No nodes found", err=True)
            raise typer.Exit(1)
        node = resources[0]["node"]

    try:
        templates = client.list_templates(node)
    except Exception as e:
        typer.echo(f"Error fetching templates: {e}", err=True)
        raise typer.Exit(1)

    if output == "json":
        print_json(templates, color)
        return

    console = Console(no_color=not color)
    table = Table(
        title=f"LXC Templates (node: {node})",
        title_style=Style(bold=True),
        header_style=(
            Style(color="cyan", bold=True) if color else Style(bold=True)
        ),
        border_style="blue" if color else None,
    )
    table.add_column("Template")
    table.add_column("OS")
    table.add_column("Version")
    table.add_column("Status")
    table.add_column("Type")

    for t in templates:
        template_name = t.get("template", "")
        manage = t.get("manage", 0)
        status = "downloaded" if manage else "available"
        table.add_row(
            template_name,
            t.get("os", ""),
            t.get("version", ""),
            status,
            t.get("type", ""),
        )

    console.print(table)


@template_app.command("download")
def template_download(
    template: str = typer.Argument(..., help="Template name to download"),
    node: str | None = typer.Option(None, "--node", "-n", help="Node name"),
    wait: bool = typer.Option(False, "--wait", help="Wait for download to complete"),
):
    """Download an LXC template."""
    client = get_client()

    if not node:
        resources = client.list_resources("node")
        if not resources:
            typer.echo("Error: No nodes found", err=True)
            raise typer.Exit(1)
        node = resources[0]["node"]

    typer.echo(f"Downloading template '{template}' on node {node}... ", nl=False)
    try:
        data = client.download_template(node, template)
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


@template_app.command("remove")
def template_remove(
    template: str = typer.Argument(..., help="Template name to remove"),
    storage: str = typer.Option("local", "--storage", "-s", help="Storage pool"),
    node: str | None = typer.Option(None, "--node", "-n", help="Node name"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Remove a downloaded LXC template."""
    client = get_client()

    if not node:
        resources = client.list_resources("node")
        if not resources:
            typer.echo("Error: No nodes found", err=True)
            raise typer.Exit(1)
        node = resources[0]["node"]

    volid = f"{storage}:vztmpl/{template}"

    if not force:
        typer.confirm(f"Remove template '{template}' from {storage}?", abort=True)

    typer.echo("Removing template... ", nl=False)
    try:
        client.raw_delete(
            f"/api2/json/nodes/{node}/storage/{storage}/content/{volid}"
        )
        typer.echo("done")
    except Exception as e:
        typer.echo(f"failed ({e})")
        raise typer.Exit(1)
