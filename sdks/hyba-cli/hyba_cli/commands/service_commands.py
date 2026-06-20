"""
HYBA CLI - Service management commands
"""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.json import JSON
import json
from typing import Optional

from hyba_sdk import HybaClient, ConnectorConfig, ConnectorType
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
    
    api_url = config_manager.get('api_url', 'https://api.hyba.ai')
    return HybaClient(api_key=api_key, api_url=api_url)


@click.group()
def services_group():
    """Service management commands"""
    pass


@click.command()
@click.option('--name', required=True, help='Service name')
@click.option('--tier', default='production', help='Service tier (developer, production, sovereign)')
@click.option('--connector', type=str, help='Connector type')
@click.option('--host', type=str, help='Connector host')
@click.option('--database', type=str, help='Database name')
@click.option('--output-format', type=click.Choice(['json', 'table']), default='table')
def provision(name, tier, connector, host, database, output_format):
    """
    Provision a new computational intelligence service
    
    Example:
    
    \b
    $ hyba provision --name portfolio-optimizer --tier production
    ✓ Provisioned: hyba-ciaas-001 (2m 34s)
    """
    try:
        client = get_client()
        
        with console.status("[bold blue]Provisioning service..."):
            # Build connector config if provided
            connector_config = None
            if connector:
                connector_type = getattr(ConnectorType, connector.upper(), None)
                if not connector_type:
                    console.print(f"[red]✗ Unknown connector type: {connector}[/red]")
                    raise click.Exit(1)
                
                connector_kwargs = {'type': connector_type}
                if host:
                    connector_kwargs['host'] = host
                if database:
                    connector_kwargs['database'] = database
                
                connector_config = ConnectorConfig(**connector_kwargs)
            
            # Provision service
            service = client.provision_service(
                name=name,
                service_tier=tier,
                connector=connector_config
            )
        
        # Display result
        if output_format == 'json':
            result = {
                'service_id': service.service_id,
                'name': service.name,
                'state': service.state,
                'tier': service.service_tier,
            }
            console.print_json(data=result)
        else:
            console.print(Panel(
                f"[green]✓ Service provisioned[/green]\n"
                f"ID: {service.service_id}\n"
                f"Name: {service.name}\n"
                f"State: {service.state}\n"
                f"Tier: {service.service_tier}",
                title="Service Provisioned",
                border_style="green"
            ))
    except Exception as e:
        console.print(f"[red]✗ Provisioning failed: {str(e)}[/red]")
        raise click.Exit(1)


@click.command()
@click.option('--output-format', type=click.Choice(['json', 'table']), default='table')
def list_services(output_format):
    """
    List all services
    
    Example:
    
    \b
    $ hyba services list
    ID                  Name                  State      Tier
    hyba-ciaas-001      portfolio-optimizer   running    production
    """
    try:
        client = get_client()
        
        with console.status("[bold blue]Fetching services..."):
            services = client.list_services()
        
        if not services:
            console.print("[yellow]No services found[/yellow]")
            return
        
        if output_format == 'json':
            result = [
                {
                    'service_id': s.service_id,
                    'name': s.name,
                    'state': s.state,
                    'tier': s.service_tier,
                }
                for s in services
            ]
            console.print_json(data=result)
        else:
            table = Table(title="HYBA Services")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="magenta")
            table.add_column("State", style="green")
            table.add_column("Tier", style="yellow")
            
            for service in services:
                state_color = "green" if service.state == "running" else "yellow"
                table.add_row(
                    service.service_id,
                    service.name,
                    f"[{state_color}]{service.state}[/{state_color}]",
                    service.service_tier
                )
            
            console.print(table)
    except Exception as e:
        console.print(f"[red]✗ Failed to list services: {str(e)}[/red]")
        raise click.Exit(1)


@click.command()
@click.argument('service_id')
def start(service_id):
    """
    Start a service
    
    Example:
    
    \b
    $ hyba services start hyba-ciaas-001
    ✓ Service started
    """
    try:
        client = get_client()
        
        with console.status("[bold blue]Starting service..."):
            service = client.get_service(service_id)
            service.start()
        
        console.print(f"[green]✓ Service started: {service.service_id}[/green]")
    except Exception as e:
        console.print(f"[red]✗ Failed to start service: {str(e)}[/red]")
        raise click.Exit(1)


@click.command()
@click.argument('service_id')
def stop(service_id):
    """
    Stop a service
    
    Example:
    
    \b
    $ hyba services stop hyba-ciaas-001
    ✓ Service stopped
    """
    try:
        client = get_client()
        
        with console.status("[bold blue]Stopping service..."):
            service = client.get_service(service_id)
            service.stop()
        
        console.print(f"[green]✓ Service stopped: {service.service_id}[/green]")
    except Exception as e:
        console.print(f"[red]✗ Failed to stop service: {str(e)}[/red]")
        raise click.Exit(1)


@click.command()
@click.argument('service_id')
def describe(service_id):
    """
    Show detailed service information
    
    Example:
    
    \b
    $ hyba services describe hyba-ciaas-001
    """
    try:
        client = get_client()
        
        with console.status("[bold blue]Fetching service details..."):
            service = client.get_service(service_id)
        
        # Format as JSON
        details = {
            'service_id': service.service_id,
            'name': service.name,
            'state': service.state,
            'tier': service.service_tier,
            'tenancy': service.tenancy,
            'owner': service.owner,
            'created_at': service.created_at,
            'updated_at': service.updated_at,
            'usage': service.usage,
        }
        
        console.print(Panel(
            JSON.from_data(details),
            title=f"Service: {service.name}",
            border_style="blue"
        ))
    except Exception as e:
        console.print(f"[red]✗ Failed to describe service: {str(e)}[/red]")
        raise click.Exit(1)


@click.command()
@click.argument('service_id')
def delete(service_id):
    """
    Delete a service
    
    Example:
    
    \b
    $ hyba services delete hyba-ciaas-001
    """
    if not click.confirm(f"Are you sure you want to delete {service_id}?"):
        console.print("[yellow]Cancelled[/yellow]")
        return
    
    try:
        client = get_client()
        
        with console.status("[bold blue]Deleting service..."):
            service = client.get_service(service_id)
            service.delete()
        
        console.print(f"[green]✓ Service deleted: {service_id}[/green]")
    except Exception as e:
        console.print(f"[red]✗ Failed to delete service: {str(e)}[/red]")
        raise click.Exit(1)


# Register commands
services_group.add_command(list_services, name='list')
services_group.add_command(start)
services_group.add_command(stop)
services_group.add_command(describe)
services_group.add_command(delete)
