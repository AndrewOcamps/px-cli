
import typer
from rich.console import Console
from rich.style import Style
from rich.table import Table

from ..utils import get_client, print_json

firewall_app = typer.Typer(
    help="Manage firewall rules",
    no_args_is_help=True,
)


@firewall_app.command("list")
def firewall_list(
    vmid: int | None = typer.Option(None, "--vmid", help="VM/container ID"),
    node: str | None = typer.Option(None, "--node", "-n", help="Node name"),
    output: str = typer.Option(
        "table", "--output", "-o", help="Output format (table, json)"
    ),
    color: bool = typer.Option(False, "--color", "-c", help="Enable colored output"),
):
    """List firewall rules for a VM, node, or cluster."""
    client = get_client()

    if not node:
        resources = client.list_resources("node")
        if not resources:
            typer.echo("Error: No nodes found", err=True)
            raise typer.Exit(1)
        node = resources[0]["node"]

    vmtype = None
    if vmid:
        r = client.find_resource(vmid)
        if r:
            vmtype = r["type"]
        else:
            typer.echo(f"Error: VMID {vmid} not found", err=True)
            raise typer.Exit(1)

    try:
        rules = client.get_firewall_rules(node, vmtype, vmid)
    except Exception as e:
        typer.echo(f"Error fetching firewall rules: {e}", err=True)
        raise typer.Exit(1)

    if output == "json":
        print_json(rules, color)
        return

    console = Console(no_color=not color)
    title_suffix = f"VMID {vmid}" if vmid else f"Node {node}"
    table = Table(
        title=f"Firewall Rules: {title_suffix}",
        title_style=Style(bold=True),
        header_style=(
            Style(color="cyan", bold=True) if color else Style(bold=True)
        ),
        border_style="blue" if color else None,
    )
    table.add_column("Pos")
    table.add_column("Action")
    table.add_column("Type")
    table.add_column("Proto")
    table.add_column("Source")
    table.add_column("Dest")
    table.add_column("DPort")
    table.add_column("Comment")
    table.add_column("Enabled")

    for rule in rules:
        table.add_row(
            str(rule.get("pos", "")),
            rule.get("action", ""),
            rule.get("type", ""),
            rule.get("proto", ""),
            rule.get("source", ""),
            rule.get("dest", ""),
            rule.get("dport", ""),
            rule.get("comment", "") or "-",
            "yes" if rule.get("enable", 1) else "no",
        )

    console.print(table)
