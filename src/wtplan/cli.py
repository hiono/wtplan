"""wtplan CLI - Typer-based command line interface."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from typing_extensions import Annotated

from .core import ensure_inventory, workspace_path
from .inventory import load_inventory
from .mcp_server import (
    mcp,
    tool_plan,
    tool_preset_add,
    tool_preset_rm,
    tool_preset_path,
    tool_repo_add,
    tool_repo_rm,
    tool_repo_path,
)

console = Console()
app = typer.Typer(
    name="wtplan",
    help="Manage Git worktrees across multiple repositories",
    no_args_is_help=False,
)

# Subcommand groups
preset_app = typer.Typer(help="Manage preset-based workspaces")
repo_app = typer.Typer(help="Manage single repository workspaces")

app.add_typer(preset_app, name="preset")
app.add_typer(repo_app, name="repo")


@app.command()
def init(
    toolbox: Annotated[Optional[str], typer.Option("--toolbox", help="Toolbox directory path")] = None,
) -> None:
    """Initialize .wtplan.yml and workspace layout."""
    ensure_inventory(Path.cwd(), toolbox_dir=toolbox)
    inv = load_inventory(Path.cwd() / ".wtplan.yml")
    console.print("Initialized .wtplan.yml", style="green")
    if toolbox:
        console.print(f"toolbox_dir: {toolbox}")
    console.print(inv)


@app.command()
def plan(
    workspace_id: Annotated[Optional[str], typer.Option("--workspace-id", help="Workspace identifier")] = None,
) -> None:
    """Show differences between inventory and actual state."""
    res = tool_plan(workspace_id=workspace_id)
    console.print_json(data=res)


@app.command()
def completion(
    shell: Annotated[str, typer.Argument(help="Shell type")] = "bash",
) -> None:
    """Generate shell completion script."""
    if shell != "bash":
        console.print("Only bash completion is provided in v0.1", style="yellow")
        return

    script = """
_wtplan_completions() {
  local cur
  COMPREPLY=()
  cur="${COMP_WORDS[COMP_CWORD]}"
  local cmds="init plan preset repo completion"
  if [[ ${COMP_CWORD} -eq 1 ]]; then
    COMPREPLY=( $(compgen -W "${cmds}" -- "${cur}") )
    return 0
  fi
}
complete -F _wtplan_completions wtplan
"""
    print(script.strip())


# Preset subcommands
@preset_app.command("add")
def preset_add(
    preset: Annotated[str, typer.Argument(help="Preset name")],
    issue_iid: Annotated[int, typer.Argument(help="GitLab Issue IID")],
    base: Annotated[Optional[str], typer.Option("--base", help="Base directory")] = None,
    apply: Annotated[bool, typer.Option("--apply", help="Apply the plan immediately")] = False,
    force_links: Annotated[bool, typer.Option("--force-links", help="Force overwrite when syncing")] = False,
    delete_links: Annotated[bool, typer.Option("--delete-links", help="Delete extra files when syncing")] = False,
) -> None:
    """Create workspace from preset + Issue IID."""
    res = tool_preset_add(
        preset=preset,
        issue_iid=issue_iid,
        base=base,
        apply=apply,
        force_links=force_links,
        delete_links=delete_links,
    )
    console.print_json(data=res)


@preset_app.command("rm")
def preset_rm(
    preset: Annotated[str, typer.Argument(help="Preset name")],
    issue_iid: Annotated[int, typer.Argument(help="GitLab Issue IID")],
    force: Annotated[bool, typer.Option("--force", help="Force removal without safety checks")] = False,
) -> None:
    """Remove workspace from preset + Issue IID."""
    res = tool_preset_rm(
        preset=preset,
        issue_iid=issue_iid,
        force=force,
    )
    console.print_json(data=res)


@preset_app.command("path")
def preset_path(
    preset: Annotated[str, typer.Argument(help="Preset name")],
    issue_iid: Annotated[int, typer.Argument(help="GitLab Issue IID")],
) -> None:
    """Return absolute path of preset workspace (read-only reference)."""
    res = tool_preset_path(
        preset=preset,
        issue_iid=issue_iid,
    )
    print(res["path"])


# Repo subcommands
@repo_app.command("add")
def repo_add(
    repo: Annotated[str, typer.Argument(help="Repository name")],
    issue_iid: Annotated[int, typer.Argument(help="GitLab Issue IID")],
    base: Annotated[Optional[str], typer.Option("--base", help="Base directory")] = None,
    apply: Annotated[bool, typer.Option("--apply", help="Apply the plan immediately")] = False,
    force_links: Annotated[bool, typer.Option("--force-links", help="Force overwrite when syncing")] = False,
    delete_links: Annotated[bool, typer.Option("--delete-links", help="Delete extra files when syncing")] = False,
) -> None:
    """Create workspace from single repo + Issue IID."""
    res = tool_repo_add(
        repo=repo,
        issue_iid=issue_iid,
        base=base,
        apply=apply,
        force_links=force_links,
        delete_links=delete_links,
    )
    console.print_json(data=res)


@repo_app.command("rm")
def repo_rm(
    repo: Annotated[str, typer.Argument(help="Repository name")],
    issue_iid: Annotated[int, typer.Argument(help="GitLab Issue IID")],
    force: Annotated[bool, typer.Option("--force", help="Force removal without safety checks")] = False,
) -> None:
    """Remove workspace from single repo + Issue IID."""
    res = tool_repo_rm(
        repo=repo,
        issue_iid=issue_iid,
        force=force,
    )
    console.print_json(data=res)


@repo_app.command("path")
def repo_path(
    repo: Annotated[str, typer.Argument(help="Repository name")],
    issue_iid: Annotated[int, typer.Argument(help="GitLab Issue IID")],
) -> None:
    """Return absolute path of repo workspace (read-only reference)."""
    res = tool_repo_path(
        repo=repo,
        issue_iid=issue_iid,
    )
    print(res["path"])


# Backward compatibility - deprecated commands
@app.command()
def cd(
    workspace_id: Annotated[str, typer.Argument(help="Workspace identifier")],
) -> None:
    """[DEPRECATED] Change to workspace directory. Use 'preset path' or 'repo path' instead."""
    console.print(
        "[yellow]Warning: 'cd' is deprecated. Use 'wtplan preset path <preset> <issue_iid>' or 'wtplan repo path <repo> <issue_iid>' instead.[/yellow]"
    )
    raise typer.Exit(1)


@app.command()
def path(
    workspace_id: Annotated[str, typer.Argument(help="Workspace identifier")],
) -> None:
    """[DEPRECATED] Show workspace path. Use 'preset path' or 'repo path' instead."""
    console.print(
        "[yellow]Warning: 'path' is deprecated. Use 'wtplan preset path <preset> <issue_iid>' or 'wtplan repo path <repo> <issue_iid>' instead.[/yellow]"
    )
    raise typer.Exit(1)


def main() -> None:
    """Main entry point - CLI or MCP server mode."""
    if len(sys.argv) == 1:
        # No args → MCP server mode
        mcp.run()
    else:
        # Has args → CLI mode
        app()


if __name__ == "__main__":
    main()
