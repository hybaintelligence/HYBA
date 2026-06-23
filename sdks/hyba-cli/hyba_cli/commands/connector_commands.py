"""
HYBA CLI - Connector management commands
"""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


@click.group()
def connectors_group():
    """Connector management commands"""
    pass


@click.command()
def list_connectors():
    """
    List available connectors

    Example:

    \b
    $ hyba connectors list
    Type                Available
    sql_snowflake       Yes
    kafka               Yes
    s3                  Yes
    """
    table = Table(title="Available Connectors")
    table.add_column("Type", style="cyan")
    table.add_column("Description", style="magenta")

    connectors = [
        ("sql_snowflake", "Snowflake data warehouse"),
        ("sql_postgresql", "PostgreSQL database"),
        ("sql_mysql", "MySQL/MariaDB database"),
        ("kafka", "Apache Kafka streaming"),
        ("s3", "Amazon S3 storage"),
        ("http", "HTTP/REST API"),
        ("scada", "SCADA systems"),
        ("pubchem", "PubChem chemical database"),
        ("protein", "Protein sequence database"),
    ]

    for conn_type, description in connectors:
        table.add_row(conn_type, description)

    console.print(table)


@click.command()
@click.argument("connector_type")
def describe(connector_type):
    """
    Show connector details

    Example:

    \b
    $ hyba connectors describe sql_snowflake
    """
    docs = {
        "sql_snowflake": {
            "name": "Snowflake Data Warehouse",
            "description": "Connect to Snowflake cloud data warehouse",
            "auth": "Account, user, password",
            "required_params": ["account", "user", "password", "database"],
        },
        "kafka": {
            "name": "Apache Kafka",
            "description": "Connect to Kafka message broker",
            "auth": "SASL/SSL or plaintext",
            "required_params": ["broker", "topic"],
        },
    }

    if connector_type not in docs:
        console.print(f"[red]✗ Connector not found: {connector_type}[/red]")
        return

    info = docs[connector_type]
    console.print(
        Panel(
            f"Name: {info['name']}\n"
            f"Description: {info['description']}\n"
            f"Auth: {info['auth']}\n"
            f"Required: {', '.join(info['required_params'])}",
            title=connector_type,
            border_style="blue",
        )
    )


connectors_group.add_command(list_connectors, name="list")
connectors_group.add_command(describe)
