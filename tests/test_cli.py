"""
AutoHound — Attack Path Intelligence Engine
Copyright (c) 2026 Gordon Prescott. All rights reserved.

ACH Research Division
Unauthorized copying, distribution, or modification of this software
without explicit written permission from Gordon Prescott is prohibited.

This tool is intended exclusively for authorized security research 
and penetration testing engagements with written scope of work.
"""
"""Tests for CLI interface."""

import pytest
from click.testing import CliRunner
from autohound.cli import main


def test_cli_help():
    """Test CLI help output."""
    runner = CliRunner()
    result = runner.invoke(main, ['--help'])
    
    assert result.exit_code == 0
    assert 'AutoHound' in result.output
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
