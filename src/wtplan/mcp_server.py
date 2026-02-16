from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from .core import apply_links, ensure_inventory, init_workspace_layout, plan_links, workspace_path
from .inventory import load_inventory, write_inventory
from .policy import effective_policy

mcp = FastMCP("wtplan", json_response=True)


class WorkspaceMode(str, Enum):
    """Workspace creation mode."""

    PRESET = "preset"
    REPO = "repo"


def _workspace_add(
    mode: WorkspaceMode,
    identifier: str,
    issue_iid: int,
    base: str | None = None,
    apply: bool = False,
    force_links: bool = False,
    delete_links: bool = False,
) -> dict[str, Any]:
    """Unified workspace creation logic."""
    base_dir = Path.cwd()
    inv = load_inventory(base_dir / ".wtplan.yml")

    # Resolve workspace parameters based on mode
    preset = identifier if mode == WorkspaceMode.PRESET else None
    repo = identifier if mode == WorkspaceMode.REPO else None

    # Validate and compute path
    try:
        ws_path = workspace_path(inv, base_dir, preset=preset, iid=issue_iid, repo=repo)
    except KeyError as e:
        return {"error": f"Unknown {mode.value}: {identifier}", "details": str(e)}

    pol = effective_policy(inv, cli_force=force_links, cli_delete=delete_links)
    planned = plan_links(inv, base_dir, pol)

    result: dict[str, Any] = {
        "apply": apply,
        "base": base,
        mode.value: identifier,
        "issue_iid": issue_iid,
    }

    if not apply:
        result["plan"] = [p.__dict__ for p in planned]
        if mode == WorkspaceMode.REPO:
            result["workspace"] = str(ws_path)
            result["mode"] = "single_repo"
        return result

    applied = apply_links(inv, base_dir, pol)
    result["result"] = [p.__dict__ for p in applied]
    if mode == WorkspaceMode.REPO:
        result["workspace"] = str(ws_path)
        result["mode"] = "single_repo"

    return result


def _workspace_path(
    mode: WorkspaceMode,
    identifier: str,
    issue_iid: int,
) -> dict[str, Any]:
    """Unified path resolution."""
    base_dir = Path.cwd()
    inv = load_inventory(base_dir / ".wtplan.yml")
    preset = identifier if mode == WorkspaceMode.PRESET else None
    repo = identifier if mode == WorkspaceMode.REPO else None
    p = workspace_path(inv, base_dir, preset=preset, iid=issue_iid, repo=repo)
    result: dict[str, Any] = {
        "path": str(p),
        mode.value: identifier,
        "issue_iid": issue_iid,
    }
    if mode == WorkspaceMode.REPO:
        result["mode"] = "single_repo"
    return result


def _workspace_remove(
    mode: WorkspaceMode,
    identifier: str,
    issue_iid: int,
    force: bool = False,
    apply: bool = False,
) -> dict[str, Any]:
    """Unified removal stub."""
    result: dict[str, Any] = {
        "apply": apply,
        "force": force,
        "note": "safe delete (dirty/unpushed/diverged/unknown) is not implemented in v0.1",
        mode.value: identifier,
        "issue_iid": issue_iid,
    }
    if mode == WorkspaceMode.REPO:
        result["mode"] = "single_repo"
    return result


def _create_workspace_prompt(mode: str, identifier_name: str, identifier: str, issue_iid: int, base: str | None = None) -> str:
    """Unified workspace creation prompt."""
    b = base or ""
    args = f"{identifier_name}: '{identifier}', issue_iid: {issue_iid}, base: '{b}', apply: false"
    desc = "preset" if mode == "preset" else "single repo (no preset defined)"
    return (
        f"Create workspace from Issue IID using {desc}.\n"
        f"1) Get plan (apply=false)\n"
        f"   tools/call: {mode}__add {{{args}}}\n"
        f"2) Review the plan, then execute with apply=true if no issues\n"
        f"   tools/call: {mode}_add {{..., apply: true}}\n"
    )


def _safe_remove_prompt(mode: str, identifier_name: str, identifier: str, issue_iid: int) -> str:
    """Unified safe removal prompt."""
    msg = "Before removing workspace, check status (dirty/unpushed/diverged/unknown) and ask whether force is appropriate."
    args = f"{identifier_name}: '{identifier}', issue_iid: {issue_iid}, force: false, apply: false"
    call = f"tools/call: {mode}_rm {{{args}}}"
    return f"{msg}\n{call}\n"


@mcp.tool(name="init")
def tool_init(toolbox_dir: str | None = None, config_path: str | None = None) -> dict[str, Any]:
    """Initialize inventory, prepare bare repository, optionally enable toolbox."""
    base = Path.cwd()
    inv_path = Path(config_path) if config_path else base / ".wtplan.yml"
    try:
        inv = load_inventory(inv_path)
    except FileNotFoundError:
        ensure_inventory(base, toolbox_dir=toolbox_dir)
        inv = load_inventory(inv_path)
    if toolbox_dir and "toolbox_dir" not in inv:
        inv["toolbox_dir"] = toolbox_dir
        write_inventory(inv_path, inv)
    layout = init_workspace_layout(inv, base)
    return {"inventory": str(inv_path), "layout": layout}


@mcp.tool(name="plan")
def tool_plan(workspace_id: str | None = None) -> dict[str, Any]:
    """Summarize differences between inventory and actual state (create/delete/update)."""
    base = Path.cwd()
    inv_path = base / ".wtplan.yml"
    try:
        inv = load_inventory(inv_path)
    except FileNotFoundError:
        return {"error": f"Inventory not found: {inv_path}. Run 'wtplan init' first."}
    pol = effective_policy(inv, cli_force=False, cli_delete=False)
    items = [pi.__dict__ for pi in plan_links(inv, base, pol)]
    return {"links_repo_root": items, "note": "git worktree operations are not implemented in v0.1"}


@mcp.tool(name="preset_add")
def tool_preset_add(
    preset: str,
    issue_iid: int,
    base: str | None = None,
    apply: bool | None = False,
    force_links: bool | None = False,
    delete_links: bool | None = False,
) -> dict[str, Any]:
    """Create workspace from preset + Issue IID (plan → confirm → apply)."""
    return _workspace_add(
        WorkspaceMode.PRESET, preset, issue_iid, base, apply or False, force_links or False, delete_links or False
    )


@mcp.tool(name="repo_add")
def tool_repo_add(
    repo: str,
    issue_iid: int,
    base: str | None = None,
    apply: bool | None = False,
    force_links: bool | None = False,
    delete_links: bool | None = False,
) -> dict[str, Any]:
    """Create workspace from single repo + Issue IID (no preset required)."""
    return _workspace_add(
        WorkspaceMode.REPO, repo, issue_iid, base, apply or False, force_links or False, delete_links or False
    )


@mcp.tool(name="preset_rm")
def tool_preset_rm(
    preset: str,
    issue_iid: int,
    force: bool | None = False,
    apply: bool | None = False,
) -> dict[str, Any]:
    """Safely remove workspace from preset + Issue IID (v0.1 is a stub)."""
    return _workspace_remove(WorkspaceMode.PRESET, preset, issue_iid, force or False, apply or False)


@mcp.tool(name="repo_rm")
def tool_repo_rm(
    repo: str,
    issue_iid: int,
    force: bool | None = False,
    apply: bool | None = False,
) -> dict[str, Any]:
    """Safely remove workspace from single repo + Issue IID (v0.1 is a stub)."""
    return _workspace_remove(WorkspaceMode.REPO, repo, issue_iid, force or False, apply or False)


@mcp.tool(name="preset_path")
def tool_preset_path(preset: str, issue_iid: int) -> dict[str, Any]:
    """Return absolute path of workspace from preset + Issue IID (read-only reference)."""
    return _workspace_path(WorkspaceMode.PRESET, preset, issue_iid)


@mcp.tool(name="repo_path")
def tool_repo_path(repo: str, issue_iid: int) -> dict[str, Any]:
    """Return absolute path of workspace from single repo + Issue IID (read-only reference)."""
    return _workspace_path(WorkspaceMode.REPO, repo, issue_iid)


@mcp.prompt(name="create_preset_workspace")
def prompt_create_preset_workspace(preset: str, issue_iid: int, base: str | None = None) -> str:
    """Create workspace from preset + Issue IID."""
    return _create_workspace_prompt("preset", "preset", preset, issue_iid, base)


@mcp.prompt(name="create_repo_workspace")
def prompt_create_repo_workspace(repo: str, issue_iid: int, base: str | None = None) -> str:
    """Create workspace from single repo + Issue IID."""
    return _create_workspace_prompt("repo", "repo", repo, issue_iid, base)


@mcp.prompt(name="review_workspace_plan")
def prompt_review_workspace_plan(workspace_id: str | None = None) -> str:
    return (
        "Summarize the plan content, highlighting CONFLICT/UPDATE/DELETE.\n"
        "Especially warn about destructive changes when delete-links (rsync -a --delete equivalent) is involved.\n"
    )


@mcp.prompt(name="safe_remove_preset")
def prompt_safe_remove_preset(preset: str, issue_iid: int) -> str:
    """Safely remove workspace from preset + Issue IID."""
    return _safe_remove_prompt("preset", "preset", preset, issue_iid)


@mcp.prompt(name="safe_remove_repo")
def prompt_safe_remove_repo(repo: str, issue_iid: int) -> str:
    """Safely remove workspace from single repo + Issue IID."""
    return _safe_remove_prompt("repo", "repo", repo, issue_iid)
