"""Tests for the CLI entry point."""

import sys
from unittest.mock import patch

from pace.cli import main


def test_main_returns_zero() -> None:
    """Test that main returns 0."""
    with patch.object(sys, "argv", ["pace", "init"]):
        assert main() == 0
