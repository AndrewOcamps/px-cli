import getpass
import os

import requests
import typer

from ..client import ProxmoxClient
from ..config import CONFIG_PATH, load_config, remove_config, write_config


def _prompt_endpoint(default: str) -> str:
    prompt = "    Proxmox endpoint"
    if default:
        prompt += f" [{default}]"
    prompt += ": "
    value = input(prompt).strip()
    if not value and default:
        return default
    if not value:
        while not value:
            value = input("    Endpoint cannot be empty: ").strip()
    if not value.startswith("http"):
        value = f"https://{value}"
    return value


def _prompt_username(default: str = "") -> str:
    prompt = "    Username (e.g. root@pam)"
    if default:
        prompt += f" [{default}]"
    prompt += ": "
    value = input(prompt).strip()
    if not value and default:
        return default
    if not value:
        while not value:
            value = input("    Username cannot be empty: ").strip()
    return value


def _prompt_password() -> str:
    password = getpass.getpass("    Password: ").strip()
    while not password:
        password = getpass.getpass("    Password cannot be empty: ").strip()
    return password


def login(
    endpoint: str = typer.Option("", "--endpoint", "-e", help="Proxmox endpoint URL"),
    username: str = typer.Option("", "--username", "-u", help="Proxmox username"),
):
    """Authenticate and configure Proxmox connection.

    Prompts for endpoint, username and password, then creates a
    reusable API token and saves it to ~/.proxmox/config.
    """
    existing = None
    if os.path.exists(CONFIG_PATH):
        try:
            existing = load_config()
        except Exception:
            pass

    typer.echo()

    ep = endpoint or _prompt_endpoint(existing.endpoint if existing else "")
    user = username or _prompt_username()
    password = _prompt_password()
    token_id = "px-cli"

    typer.echo()
    client = ProxmoxClient(ep)

    try:
        client.login(user, password)
    except requests.RequestException as e:
        status = ""
        if hasattr(e, "response") and e.response is not None:
            status = f" (HTTP {e.response.status_code})"
        typer.echo(f"  Authentication failed{status}")
        raise typer.Exit(1)

    typer.echo(f"  \u2713 Authenticated as {user}")

    typer.echo(f"  \u2192 Creating API token '{token_id}'... ", nl=False)
    try:
        token_data = client.create_token(
            user, token_id, comment="Created by px login"
        )
        token_value = token_data.get("value", "")
        full_token_id = token_data.get("full-tokenid", f"{user}!{token_id}")
        full_token = f"{full_token_id}={token_value}"
        typer.echo("done")
    except requests.RequestException as e:
        status = ""
        detail = ""
        if hasattr(e, "response") and e.response is not None:
            status = f" (HTTP {e.response.status_code})"
            try:
                detail = e.response.json().get("errors", "")
                if isinstance(detail, dict):
                    detail = "; ".join(f"{k}: {v}" for k, v in detail.items())
            except Exception:
                pass
        typer.echo(f"failed{status}")
        if detail:
            typer.echo(f"    {detail}")
        typer.echo(
            "\n  Could not create API token. You may not have the required\n"
            "  permissions. Create a token manually in the Proxmox UI and\n"
            f"  add it to {CONFIG_PATH}:\n"
            f"    endpoint={ep}\n"
            f"    token=user@realm!tokenid=secret"
        )
        raise typer.Exit(1)

    path = write_config(ep, full_token)
    typer.echo(f"  \u2713 Configuration saved to {path}")

    typer.echo("  \u2192 Verifying token... ", nl=False)
    verify_client = ProxmoxClient(ep, token=full_token)
    try:
        verify_client.whoami()
        typer.echo("ok")
    except Exception:
        typer.echo("warning (token may not work)")

    typer.echo()
    typer.echo("  Ready. Try:")
    typer.echo("    px vm list")


def logout():
    """Remove Proxmox configuration from ~/.proxmox/config."""
    if not os.path.exists(CONFIG_PATH):
        typer.echo("  No configuration found.")
        raise typer.Exit(0)

    typer.echo()
    typer.confirm(
        "  This will remove your Proxmox configuration. Continue?",
        abort=True,
    )

    backup = remove_config()
    typer.echo(f"  \u2713 Configuration removed (backup saved to {backup})")
