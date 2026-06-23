"""
HYBA CLI - Workload execution commands
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.json import JSON
import json
from datetime import datetime, timedelta

from hyba_sdk import HybaClient
from hyba_cli.utils.auth import AuthManager
from hyba_cli.utils.config import ConfigManager

console = Console()
auth_manager = AuthManager()
config_manager = ConfigManager()


def get_client() -> HybaClient:
    """Get authenticated HYBA client"""
    api_key = auth_manager.get_api_key()
    if not api_key:
        console.print("[red]✗ Not authenticated. Run 'hyba login' first.[/red]")
        raise click.Exit(1)

    api_url = config_manager.get("api_url", "https://api.hyba.ai")
    return HybaClient(api_key=api_key, api_url=api_url)


@click.command()
@click.argument("service_id")
@click.option("--workload", default="explain", help="Workload type")
@click.option("--context", required=True, help="Workload context/input")
@click.option("--output", type=click.Path(), help="Output file path")
@click.option("--timeout", type=int, default=300, help="Execution timeout (seconds)")
def execute(service_id, workload, context, output, timeout):
    """
    Execute a workload on a service
    
    Example:
    
    \b
    $ hyba execute portfolio-optimizer \\
    >   --workload explain \\
    >   --context "Portfolio optimization strategy"
    """
    try:
        client = get_client()

        with console.status("[bold blue]Executing workload..."):
            service = client.get_service(service_id)
            result = service.execute(workload=workload, context=context)

        if output:
            with open(output, "w") as f:
                json.dump(result, f, indent=2)
            console.print(f"[green]✓ Results saved to {output}[/green]")
        else:
            # Display results
            console.print(
                Panel(
                    JSON.from_data(result),
                    title=f"Workload Result: {workload}",
                    border_style="green",
                )
            )
    except Exception as e:
        console.print(f"[red]✗ Execution failed: {str(e)}[/red]")
        raise click.Exit(1)


@click.command()
@click.argument("service_id")
@click.option("--output", type=click.Path(), help="Output file path")
@click.option("--stream", is_flag=True, help="Stream results continuously")
@click.option("--format", type=click.Choice(["json", "table"]), default="json")
def results(service_id, output, stream, format):
    """
    Get workload results

    Example:

    \b
    $ hyba results portfolio-optimizer
    $ hyba results portfolio-optimizer --stream
    """
    try:
        client = get_client()
        service = client.get_service(service_id)

        # For now, just get service details as placeholder
        with console.status("[bold blue]Fetching results..."):
            result = service.refresh()

        if output:
            with open(output, "w") as f:
                json.dump({"service": service.name, "state": service.state}, f)
            console.print(f"[green]✓ Results saved to {output}[/green]")
        else:
            console.print(
                Panel(
                    JSON.from_data(
                        {
                            "service_id": service.service_id,
                            "name": service.name,
                            "state": service.state,
                            "usage": service.usage,
                        }
                    ),
                    title="Service Results",
                    border_style="blue",
                )
            )
    except Exception as e:
        console.print(f"[red]✗ Failed to get results: {str(e)}[/red]")
        raise click.Exit(1)


@click.command()
@click.argument("service_id")
@click.option("--limit", type=int, default=10, help="Number of items to show")
@click.option("--days", type=int, default=7, help="Historical days to retrieve")
def history(service_id, limit, days):
    """
    Show execution history for a service

    Example:

    \b
    $ hyba history portfolio-optimizer --limit 20 --days 30
    """
    try:
        client = get_client()

        with console.status("[bold blue]Fetching history..."):
            service = client.get_service(service_id)

        # Placeholder - would fetch from API in real implementation
        console.print(f"[yellow]Execution history for {service.name}[/yellow]")
        console.print(f"Service ID: {service_id}")
        console.print(f"State: {service.state}")
        console.print(f"Usage: {service.usage}")
    except Exception as e:
        console.print(f"[red]✗ Failed to get history: {str(e)}[/red]")
        raise click.Exit(1)
