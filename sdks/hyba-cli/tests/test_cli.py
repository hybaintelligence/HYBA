"""
Tests for HYBA CLI
"""

import pytest
from click.testing import CliRunner
from hyba_cli.cli import main


@pytest.fixture
def cli_runner():
    """Get CLI runner"""
    return CliRunner()


def test_cli_help(cli_runner):
    """Test CLI help output"""
    result = cli_runner.invoke(main, ['--help'])
    assert result.exit_code == 0
    assert 'HYBA CLI' in result.output


def test_cli_version(cli_runner):
    """Test CLI version output"""
    result = cli_runner.invoke(main, ['--version'])
    assert result.exit_code == 0
    assert '0.1.0' in result.output


def test_login_required(cli_runner):
    """Test that login is required for most commands"""
    result = cli_runner.invoke(main, ['services', 'list'])
    assert result.exit_code != 0


def test_connectors_list(cli_runner):
    """Test listing connectors"""
    result = cli_runner.invoke(main, ['connectors', 'list'])
    assert result.exit_code == 0
    assert 'sql_snowflake' in result.output
