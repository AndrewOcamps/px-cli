"""
px — Proxmox CLI

Usage: px <group> <command> [options]

A command-line tool for managing Proxmox VE clusters,
VMs, containers, storage, backups, and more.
"""

import typer

from .commands.backup import backup_app
from .commands.cluster import cluster_app
from .commands.firewall import firewall_app
from .commands.login import login, logout
from .commands.node import node_app
from .commands.pool import pool_app
from .commands.storage import storage_app
from .commands.template import template_app
from .commands.vm import vm_app

app = typer.Typer(
    name="px",
    help="px — Proxmox CLI: manage VMs, containers, storage, backups, and more.",
    no_args_is_help=True,
)

app.command(name="login")(login)
app.command(name="logout")(logout)
app.add_typer(vm_app, name="vm", help="Manage VMs and containers")
app.add_typer(storage_app, name="storage", help="Manage storage pools and contents")
app.add_typer(backup_app, name="backup", help="Manage VM/container backups")
app.add_typer(template_app, name="template", help="Manage LXC templates")
app.add_typer(node_app, name="node", help="Manage Proxmox nodes")
app.add_typer(pool_app, name="pool", help="Manage resource pools")
app.add_typer(cluster_app, name="cluster", help="Cluster information")
app.add_typer(firewall_app, name="firewall", help="Manage firewall rules")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
