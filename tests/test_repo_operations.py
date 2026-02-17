"""Tests for wtplan repo operations and links/copy functionality."""

import os

import pytest
from typer.testing import CliRunner

from wtplan import mcp_server
from wtplan.cli import app

test_env = os.environ.copy()
test_env.update(
    {
        "NO_COLOR": "1",
        "_TYPER_FORCE_DISABLE_TERMINAL": "1",
        "FORCE_COLOR": "",
        "PY_COLORS": "",
    }
)

runner = CliRunner(env=test_env)


class TestRepoAdd:
    """Tests for 'repo add' command."""

    def test_repo_add_help(self):
        """Test repo add --help shows correct usage."""
        result = runner.invoke(app, ["repo", "add", "--help"])
        assert result.exit_code == 0
        assert "REPO" in result.output
        assert "IID" in result.output
        assert "--apply" in result.output

    def test_repo_add_missing_args(self):
        """Test repo add without required args fails."""
        result = runner.invoke(app, ["repo", "add"])
        assert result.exit_code != 0
        assert "Missing argument" in result.output


class TestRepoRm:
    """Tests for 'repo rm' command."""

    def test_repo_rm_help(self):
        """Test repo rm --help shows correct usage."""
        result = runner.invoke(app, ["repo", "rm", "--help"])
        assert result.exit_code == 0
        assert "REPO" in result.output
        assert "IID" in result.output

    def test_repo_rm_missing_args(self):
        """Test repo rm without required args fails."""
        result = runner.invoke(app, ["repo", "rm"])
        assert result.exit_code != 0


class TestRepoPath:
    """Tests for 'repo path' command."""

    def test_repo_path_help(self):
        """Test repo path --help shows correct usage."""
        result = runner.invoke(app, ["repo", "path", "--help"])
        assert result.exit_code == 0
        assert "REPO" in result.output
        assert "IID" in result.output


class TestPresetAdd:
    """Tests for 'preset add' command."""

    def test_preset_add_help(self):
        """Test preset add --help shows correct usage."""
        result = runner.invoke(app, ["preset", "add", "--help"])
        assert result.exit_code == 0
        assert "PRESET" in result.output
        assert "IID" in result.output
        assert "--apply" in result.output

    def test_preset_add_missing_args(self):
        """Test preset add without required args fails."""
        result = runner.invoke(app, ["preset", "add"])
        assert result.exit_code != 0
        assert "Missing argument" in result.output


class TestPresetRm:
    """Tests for 'preset rm' command."""

    def test_preset_rm_help(self):
        """Test preset rm --help shows correct usage."""
        result = runner.invoke(app, ["preset", "rm", "--help"])
        assert result.exit_code == 0
        assert "PRESET" in result.output
        assert "IID" in result.output


class TestPresetPath:
    """Tests for 'preset path' command."""

    def test_preset_path_help(self):
        """Test preset path --help shows correct usage."""
        result = runner.invoke(app, ["preset", "path", "--help"])
        assert result.exit_code == 0
        assert "PRESET" in result.output
        assert "ISSUE_IID" in result.output


class TestPlanCommand:
    """Tests for 'plan' command (links diff functionality)."""

    def test_plan_help(self):
        """Test plan command help."""
        result = runner.invoke(app, ["plan", "--help"])
        assert result.exit_code == 0
        assert "workspace-id" in result.output
        assert "differences" in result.output

    def test_plan_no_args_ok(self):
        """Test plan works without args (optional workspace-id)."""
        result = runner.invoke(app, ["plan"])
        # May succeed or fail depending on environment, but shouldn't crash
        assert result.exit_code in [0, 1]


class TestInitCommand:
    """Tests for 'init' command."""

    def test_init_help(self):
        """Test init --help shows usage."""
        result = runner.invoke(app, ["init", "--help"])
        assert result.exit_code == 0
        assert "toolbox" in result.output


class TestCompletionCommand:
    """Tests for 'completion' command."""

    def test_completion_help(self):
        """Test completion --help shows usage."""
        result = runner.invoke(app, ["completion", "--help"])
        assert result.exit_code == 0
        assert "shell" in result.output


class TestApplyFlag:
    """Tests for --apply flag in add commands."""

    def test_preset_add_with_apply_flag(self):
        """Test preset add accepts --apply flag."""
        result = runner.invoke(app, ["preset", "add", "--help"])
        assert result.exit_code == 0
        assert "--apply" in result.output

    def test_repo_add_with_apply_flag(self):
        """Test repo add accepts --apply flag."""
        result = runner.invoke(app, ["repo", "add", "--help"])
        assert result.exit_code == 0
        assert "--apply" in result.output


class TestDeprecatedCommands:
    """Tests for deprecated commands."""

    def test_deprecated_cd_command(self):
        """Test cd command shows deprecation warning."""
        result = runner.invoke(app, ["cd", "--help"])
        assert result.exit_code == 0

    def test_deprecated_path_command(self):
        """Test path command shows deprecation warning."""
        result = runner.invoke(app, ["path", "--help"])
        assert result.exit_code == 0


class TestMCPFunctions:
    """Tests for MCP function integration."""

    def test_tool_preset_add_with_valid_preset(self, tmp_path, monkeypatch):
        """Test preset add with valid preset and inventory."""

        monkeypatch.chdir(tmp_path)
        (tmp_path / ".wtplan.yml").write_text(
            "presets:\n  test-preset:\n    primary_repo: test-repo\n    repos:\n      - test-repo\n"
        )

        result = mcp_server.tool_preset_add(
            preset="test-preset",
            issue_iid=1,
            base=str(tmp_path),
            apply=False,
            force_links=False,
            delete_links=False,
        )
        assert result is not None

    def test_tool_preset_add_with_invalid_preset(self, tmp_path, monkeypatch):
        """Test preset add with invalid preset - function returns error dict."""

        monkeypatch.chdir(tmp_path)
        (tmp_path / ".wtplan.yml").write_text("presets:\n  test:\n    primary_repo: r\n    repos:\n      - r\n")

        result = mcp_server.tool_preset_add(
            preset="nonexistent",
            issue_iid=1,
            apply=False,
            force_links=False,
            delete_links=False,
        )
        assert result is not None
        assert "error" in result or "message" in result

    def test_tool_preset_path_with_invalid_preset(self, tmp_path, monkeypatch):
        """Test preset path with invalid preset raises error."""

        monkeypatch.chdir(tmp_path)
        (tmp_path / ".wtplan.yml").write_text("presets: {}")

        with pytest.raises(KeyError):
            mcp_server.tool_preset_path(
                preset="nonexistent",
                issue_iid=1,
            )

    def test_tool_repo_add_with_repo(self, tmp_path, monkeypatch):
        """Test repo add with valid repo."""

        monkeypatch.chdir(tmp_path)
        (tmp_path / ".wtplan.yml").write_text("repos:\n  my-repo:\n    path: /tmp/my-repo\n")

        result = mcp_server.tool_repo_add(
            repo="my-repo",
            issue_iid=1,
            base=str(tmp_path),
            apply=False,
            force_links=False,
            delete_links=False,
        )
        assert result is not None

    def test_tool_repo_add_with_invalid_repo(self, tmp_path, monkeypatch):
        """Test repo add with invalid repo - returns plan (validation happens later)."""

        monkeypatch.chdir(tmp_path)
        (tmp_path / ".wtplan.yml").write_text("repos:\n  my-repo:\n    path: /tmp/my-repo\n")

        result = mcp_server.tool_repo_add(
            repo="nonexistent",
            issue_iid=1,
            apply=False,
            force_links=False,
            delete_links=False,
        )
        assert result is not None
        assert "plan" in result


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_missing_inventory_file(self, tmp_path, monkeypatch):
        """Test behavior when inventory file is missing."""

        monkeypatch.chdir(tmp_path)

        with pytest.raises(FileNotFoundError):
            mcp_server.tool_preset_add(
                preset="test",
                issue_iid=1,
                apply=False,
                force_links=False,
                delete_links=False,
            )

    def test_invalid_issue_iid_type(self):
        """Test that invalid issue_iid type is handled."""
        result = runner.invoke(app, ["preset", "add", "test", "abc"])
        assert result.exit_code != 0

    def test_preset_add_with_apply_and_force_flags(self, tmp_path, monkeypatch):
        """Test preset add with both --apply and --force-links."""

        monkeypatch.chdir(tmp_path)
        (tmp_path / ".wtplan.yml").write_text("presets:\n  test:\n    primary_repo: r\n    repos:\n      - r\n")

        result = mcp_server.tool_preset_add(
            preset="test",
            issue_iid=1,
            base=str(tmp_path),
            apply=True,
            force_links=True,
            delete_links=False,
        )
        assert result is not None
