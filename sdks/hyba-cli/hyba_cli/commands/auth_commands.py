"""
HYBA CLI - Authentication commands
"""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import json

from hyba_sdk import HybaClient
from hyba_cli.utils.auth import AuthManager
from hyba_cli.utils.config import ConfigManager

console = Console()
auth_manager = AuthManager()
config_manager = ConfigManager()


@click.group()
def auth_group():
    """Authentication and authorization commands"""
    pass


@click.command()
@click.option(
    "--api-key", type=str, help="API key (if not provided, you will be prompted)"
)
@click.option("--api-url", type=str, default="https://api.hyba.ai", help="API URL")
def login(api_key, api_url):
    """
    Authenticate with HYBA API

    Example:

    \b
    $ hyba login --api-key hyba_live_abc123
    ✓ Successfully authenticated as developer@hyba.ai
    """
    if not api_key:
        api_key = click.prompt("API Key", hide_input=True)

    # Validate API key format
    if not api_key.startswith("hyba_"):
        console.print("[red]✗ Invalid API key format (must start with 'hyba_')[/red]")
        raise click.Exit(1)

    # Test credentials
    try:
        with console.status("[bold blue]Validating credentials..."):
            client = HybaClient(api_key=api_key, api_url=api_url)
            health = client.health_check()

        # Save credentials
        auth_manager.save_credentials(api_key, api_url)
        config_manager.set("api_url", api_url)

        console.print(
            Panel(
                f"[green]✓ Successfully authenticated[/green]\n"
                f"API URL: {api_url}\n"
                f"API Key: {api_key[:20]}...",
                title="Authentication",
                border_style="green",
            )
        )
    except Exception as e:
        console.print(f"[red]✗ Authentication failed: {str(e)}[/red]")
        raise click.Exit(1)


@click.command()
def logout():
    """
    Logout and remove stored credentials

    Example:

    \b
    $ hyba logout
    ✓ Successfully logged out
    """
    auth_manager.clear_credentials()
    console.print("[green]✓ Successfully logged out[/green]")


@click.command()
@click.pass_context
def health(ctx):
    """
    Check API health and connectivity

    Example:

    \b
    $ hyba health
    ✓ API is healthy
    Status: operational
    """
    try:
        api_key = auth_manager.get_api_key()
        if not api_key:
            console.print("[red]✗ Not authenticated. Run 'hyba login' first.[/red]")
            raise click.Exit(1)

        api_url = config_manager.get("api_url", "https://api.hyba.ai")

        with console.status("[bold blue]Checking API health..."):
            client = HybaClient(api_key=api_key, api_url=api_url)
            health = client.health_check()

        # Display health status
        status_color = "green" if health.get("status") == "ok" else "yellow"
        console.print(
            Panel(
                f"[{status_color}]Status: {health.get('status')}[/{status_color}]\n"
                f"API URL: {api_url}\n"
                f"Uptime: {health.get('uptime', 'N/A')}",
                title="API Health",
                border_style=status_color,
            )
        )
    except Exception as e:
        console.print(f"[red]✗ Health check failed: {str(e)}[/red]")
        raise click.Exit(1)


@click.group()
def auth_commands():
    """Authentication commands"""
    pass


auth_group.add_command(login)
auth_group.add_command(logout)
