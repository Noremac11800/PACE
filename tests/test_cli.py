"""
Tests for the CLI entry point.
"""

from pace.cli import main


def test_main_returns_zero():
    """Test that main returns 0."""
    assert main() == 0
