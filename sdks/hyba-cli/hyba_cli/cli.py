"""
HYBA CLI - Main entry point
"""

import click
import sys
from pathlib import Path
from typing import Optional
import json

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.spinner import Spinner
import time

from hyba_cli.commands import (
    auth_commands,
    service_commands,
    connector_commands,
    workload_commands,
    config_commands,
)
from hyba_cli.utils.config import ConfigManager
from hyba_cli.utils.auth import AuthManager
from hyba_cli.utils.logger import setup_logging

# Initialize console for rich output
console = Console()


@click.group(invoke_without_command=True)
@click.option("--version", is_flag=True, help="Show version")
@click.option("--debug", is_flag=True, help="Enable debug output")
@click.pass_context
def main(ctx, version, debug):
    """
    HYBA CLI - Enterprise computational intelligence platform

    Provision, manage, and execute computational intelligence services.

    Quick start:

    \b
    $ hyba login
    $ hyba provision --name my-optimizer --tier production
    $ hyba execute my-optimizer --workload explain --context "Your query"

    Documentation: https://docs.hyba.ai/cli
    """
    # Setup logging
    setup_logging(debug=debug)

    if version:
        click.echo("HYBA CLI version 0.1.0")
        sys.exit(0)

    # Show help if no command specified
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# Register command groups
main.add_command(auth_commands.auth_group, name="auth")
main.add_command(auth_commands.login, name="login")
main.add_command(auth_commands.logout, name="logout")

main.add_command(service_commands.services_group, name="services")
main.add_command(service_commands.provision, name="provision")

main.add_command(workload_commands.execute, name="execute")
main.add_command(workload_commands.results, name="results")
main.add_command(workload_commands.history, name="history")

main.add_command(connector_commands.connectors_group, name="connectors")

main.add_command(config_commands.config_group, name="config")

# Top-level convenience commands
main.add_command(auth_commands.health, name="health")
main.add_command(config_commands.completion, name="completion")


if __name__ == "__main__":
    main()
