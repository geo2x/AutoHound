"""Tests for CLI interface."""

import pytest
from click.testing import CliRunner
from bloodhound_ai.cli import main


def test_cli_help():
    """Test CLI help output."""
    runner = CliRunner()
    result = runner.invoke(main, ['--help'])
    
    assert result.exit_code == 0
    assert 'BloodHound AI' in result.output
    assert '--input' in result.output
    assert '--output' in result.output


def test_cli_version():
    """Test version flag."""
    runner = CliRunner()
    result = runner.invoke(main, ['--version'])
    
    assert result.exit_code == 0
    assert '0.1.0' in result.output


def test_cli_missing_input():
    """Test that CLI fails without input."""
    runner = CliRunner()
    result = runner.invoke(main, ['--skip-auth-check'])
    
    # Should fail because --input is required
    assert result.exit_code != 0
