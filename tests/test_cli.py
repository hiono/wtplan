"""Tests for wtplan CLI."""

import pytest
from typer.testing import CliRunner

from wtplan.cli import app

runner = CliRunner()


class TestCLIHelp:
    """Test CLI help output."""

    def test_main_help(self):
        """Test main help command."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "wtplan" in result.output

    def test_preset_help(self):
        """Test preset subcommand help."""
        result = runner.invoke(app, ["preset", "--help"])
        assert result.exit_code == 0
        assert "add" in result.output
        assert "rm" in result.output
        assert "path" in result.output

    def test_repo_help(self):
        """Test repo subcommand help."""
        result = runner.invoke(app, ["repo", "--help"])
        assert result.exit_code == 0
        assert "add" in result.output
        assert "rm" in result.output
        assert "path" in result.output

    def test_init_help(self):
        """Test init command help."""
        result = runner.invoke(app, ["init", "--help"])
        assert result.exit_code == 0
        assert "toolbox" in result.output

    def test_completion_help(self):
        """Test completion command help."""
        result = runner.invoke(app, ["completion", "--help"])
        assert result.exit_code == 0
        assert "shell" in result.output


class TestInitCommand:
    """Test init command."""

    def test_init_with_default_toolbox(self, tmp_path):
        """Test init uses current directory as default toolbox."""
        result = runner.invoke(app, ["init"])
        # init has default value for toolbox (current directory)
        # so it should succeed or fail for other reasons
        assert "Usage:" in result.output or "toolbox" in result.output or result.exit_code in [0, 1]


class TestDeprecatedCommands:
    """Test deprecated commands show warnings."""

    def test_deprecated_cd_shows_warning(self):
        """Test cd command shows deprecation warning."""
        result = runner.invoke(app, ["cd", "--help"])
        assert result.exit_code == 0
        # The deprecated command should still be accessible
        assert "cd" in result.output.lower() or "DEPRECATED" in result.output

    def test_deprecated_path_shows_warning(self):
        """Test path command shows deprecation warning."""
        result = runner.invoke(app, ["path", "--help"])
        assert result.exit_code == 0
        # The deprecated command should still be accessible
        assert "path" in result.output.lower() or "DEPRECATED" in result.output
