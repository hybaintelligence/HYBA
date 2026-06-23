"""
HYBA CLI - Configuration commands
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
import yaml

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


config_group.add_command(show)
config_group.add_command(set_config, name="set")
config_group.add_command(get_config, name="get")
config_group.add_command(path)
