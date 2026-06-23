"""
HYBA CLI - Configuration commands
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
import yaml
import secrets
import base64

from hyba_cli.utils.config import ConfigManager

console = Console()
config_manager = ConfigManager()


@click.group()
def config_group():
    """Configuration management commands"""
    pass


@click.command()
def show():
    """
    Show current configuration

    Example:

    \b
    $ hyba config show
    """
    config = config_manager.load()

    yaml_str = yaml.dump(config, default_flow_style=False)
    syntax = Syntax(yaml_str, "yaml", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title="Configuration", border_style="blue"))


@click.command()
@click.argument("key")
@click.argument("value")
def set_config(key, value):
    """
    Set configuration value

    Example:

    \b
    $ hyba config set api_url https://api.hyba.ai
    """
    config_manager.set(key, value)
    console.print(f"[green]✓ Set {key} = {value}[/green]")


@click.command()
@click.argument("key")
def get_config(key):
    """Get configuration value"""
    value = config_manager.get(key)
    if value is None:
        console.print(f"[yellow]Key not found: {key}[/yellow]")
    else:
        console.print(f"{key}: {value}")


@click.command()
def path():
    """
    Show configuration file path

    Example:

    \b
    $ hyba config path
    ~/.hyba/config.yaml
    """
    config_path = config_manager.config_path
    console.print(str(config_path))


@click.command()
def completion(shell):
    """
    Generate shell completion

    Example:

    \b
    $ eval "$(hyba completion bash)"
    """
    if shell == "bash":
        console.print("# Bash completion (placeholder)")
    elif shell == "zsh":
        console.print("# Zsh completion (placeholder)")
    elif shell == "fish":
        console.print("# Fish completion (placeholder)")


@click.command()
@click.option(
    '--type',
    type=click.Choice(['jwt', 'password', 'api-key', 'health-token', 'operator-creds', 'all']),
    default='all',
    help='Type of secret to generate'
)
@click.option(
    '--length',
    type=int,
    default=64,
    help='Length of the secret (for jwt, password, api-key, health-token)'
)
def generate_secrets(type, length):
    """
    Generate secure secrets for configuration
    
    Example:
    
    \b
    $ hyba config generate-secrets --type all
    JWT_SECRET: a1b2c3d4e5f6...
    HYBA_INTERNAL_HEALTH_TOKEN: x9y8z7w6v5u4...
    """
    secrets_dict = {}
    
    if type in ['jwt', 'all']:
        jwt_secret = secrets.token_hex(32)
        secrets_dict['JWT_SECRET'] = jwt_secret
    
    if type in ['password', 'all']:
        password = secrets.token_urlsafe(length)
        secrets_dict['DATABASE_PASSWORD'] = password
    
    if type in ['api-key', 'all']:
        api_key = f"hyba_{secrets.token_urlsafe(32)}"
        secrets_dict['HYBA_API_KEY_SECRET'] = api_key
    
    if type in ['health-token', 'all']:
        health_token = secrets.token_hex(32)
        secrets_dict['HYBA_INTERNAL_HEALTH_TOKEN'] = health_token
    
    if type in ['operator-creds', 'all']:
        operator_creds = base64.b64encode(f"operator:{secrets.token_urlsafe(16)}".encode()).decode()
        secrets_dict['HYBA_OPERATOR_CREDENTIALS'] = operator_creds
    
    console.print(Panel(
        "\n".join([f"[green]{k}:[/green] {v}" for k, v in secrets_dict.items()]),
        title="Generated Secrets",
        border_style="green"
    ))
    
    console.print("\n[yellow]⚠ Copy these secrets to your .env file immediately![/yellow]")


config_group.add_command(show)
config_group.add_command(set_config, name="set")
config_group.add_command(get_config, name="get")
config_group.add_command(path)
config_group.add_command(generate_secrets, name='generate-secrets')
