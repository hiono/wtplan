from __future__ import annotations

from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from .core import apply_links, ensure_inventory, init_workspace_layout, plan_links, workspace_path
from .inventory import load_inventory, write_inventory
from .policy import effective_policy

mcp = FastMCP("wtplan", json_response=True)


@mcp.tool(name="init")
def tool_init(toolbox_dir: str | None = None, config_path: str | None = None) -> dict[str, Any]:
    """Initialize inventory, prepare bare repository, optionally enable toolbox."""
    base = Path.cwd()
    inv_path = Path(config_path) if config_path else base / ".wtplan.yml"
    if not inv_path.exists():
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
    inv = load_inventory(base / ".wtplan.yml")
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
    base_dir = Path.cwd()
    inv = load_inventory(base_dir / ".wtplan.yml")
    pol = effective_policy(inv, cli_force=bool(force_links), cli_delete=bool(delete_links))
    planned = plan_links(inv, base_dir, pol)
    if not apply:
        return {"apply": False, "plan": [p.__dict__ for p in planned], "base": base}
    applied = apply_links(inv, base_dir, pol)
    return {"apply": True, "result": [p.__dict__ for p in applied], "base": base}


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
    base_dir = Path.cwd()
    inv = load_inventory(base_dir / ".wtplan.yml")
    pol = effective_policy(inv, cli_force=bool(force_links), cli_delete=bool(delete_links))
    ws_path = workspace_path(inv, base_dir, preset=None, iid=issue_iid, repo=repo)
    planned = plan_links(inv, base_dir, pol)
    if not apply:
        return {
            "apply": False,
            "plan": [p.__dict__ for p in planned],
            "base": base,
            "workspace": str(ws_path),
            "mode": "single_repo",
        }
    applied = apply_links(inv, base_dir, pol)
    return {
        "apply": True,
        "result": [p.__dict__ for p in applied],
        "base": base,
        "workspace": str(ws_path),
        "mode": "single_repo",
    }


@mcp.tool(name="preset_rm")
def tool_preset_rm(
    preset: str,
    issue_iid: int,
    force: bool | None = False,
    apply: bool | None = False,
) -> dict[str, Any]:
    """Safely remove workspace from preset + Issue IID (v0.1 is a stub)."""
    return {
        "apply": bool(apply),
        "force": bool(force),
        "note": "safe delete (dirty/unpushed/diverged/unknown) is not implemented in v0.1",
        "preset": preset,
        "issue_iid": issue_iid,
    }


@mcp.tool(name="repo_rm")
def tool_repo_rm(
    repo: str,
    issue_iid: int,
    force: bool | None = False,
    apply: bool | None = False,
) -> dict[str, Any]:
    """Safely remove workspace from single repo + Issue IID (v0.1 is a stub)."""
    return {
        "apply": bool(apply),
        "force": bool(force),
        "note": "safe delete (dirty/unpushed/diverged/unknown) is not implemented in v0.1",
        "mode": "single_repo",
        "repo": repo,
        "issue_iid": issue_iid,
    }


@mcp.tool(name="preset_path")
def tool_preset_path(preset: str, issue_iid: int) -> dict[str, Any]:
    """Return absolute path of workspace from preset + Issue IID (read-only reference)."""
    base_dir = Path.cwd()
    inv = load_inventory(base_dir / ".wtplan.yml")
    p = workspace_path(inv, base_dir, preset=preset, iid=issue_iid, repo=None)
    return {"path": str(p), "preset": preset, "issue_iid": issue_iid}


@mcp.tool(name="repo_path")
def tool_repo_path(repo: str, issue_iid: int) -> dict[str, Any]:
    """Return absolute path of workspace from single repo + Issue IID (read-only reference)."""
    base_dir = Path.cwd()
    inv = load_inventory(base_dir / ".wtplan.yml")
    p = workspace_path(inv, base_dir, preset=None, iid=issue_iid, repo=repo)
    return {"path": str(p), "repo": repo, "issue_iid": issue_iid, "mode": "single_repo"}


@mcp.prompt(name="create_preset_workspace")
def prompt_create_preset_workspace(preset: str, issue_iid: int, base: str | None = None) -> str:
    """Create workspace from preset + Issue IID."""
    b = base or ""
    args = f"preset: '{preset}', issue_iid: {issue_iid}, base: '{b}', apply: false"
    return (
        "Create workspace from Issue IID using preset.\n"
        "1) Get plan (apply=false)\n"
        f"   tools/call: preset_add {{{args}}}\n"
        "2) Review the plan, then execute with apply=true if no issues\n"
        "   tools/call: preset_add {..., apply: true}\n"
    )


@mcp.prompt(name="create_repo_workspace")
def prompt_create_repo_workspace(repo: str, issue_iid: int, base: str | None = None) -> str:
    """Create workspace from single repo + Issue IID."""
    b = base or ""
    args = f"repo: '{repo}', issue_iid: {issue_iid}, base: '{b}', apply: false"
    return (
        "Create workspace from single repo (no preset defined).\n"
        "1) Get plan (apply=false)\n"
        f"   tools/call: repo_add {{{args}}}\n"
        "2) Review the plan, then execute with apply=true if no issues\n"
        "   tools/call: repo_add {..., apply: true}\n"
    )


@mcp.prompt(name="review_workspace_plan")
def prompt_review_workspace_plan(workspace_id: str | None = None) -> str:
    return (
        "Summarize the plan content, highlighting CONFLICT/UPDATE/DELETE.\n"
        "Especially warn about destructive changes when delete-links (rsync -a --delete equivalent) is involved.\n"
    )


@mcp.prompt(name="safe_remove_preset")
def prompt_safe_remove_preset(preset: str, issue_iid: int) -> str:
    """Safely remove workspace from preset + Issue IID."""
    msg = "Before removing workspace, check status (dirty/unpushed/diverged/unknown) and ask whether force is appropriate."
    args = f"preset: '{preset}', issue_iid: {issue_iid}, force: false, apply: false"
    call = f"tools/call: preset_rm {{{args}}}"
    return f"{msg}\n{call}\n"


@mcp.prompt(name="safe_remove_repo")
def prompt_safe_remove_repo(repo: str, issue_iid: int) -> str:
    """Safely remove workspace from single repo + Issue IID."""
    msg = "Before removing workspace, check status (dirty/unpushed/diverged/unknown) and ask whether force is appropriate."
    args = f"repo: '{repo}', issue_iid: {issue_iid}, force: false, apply: false"
    call = f"tools/call: repo_rm {{{args}}}"
    return f"{msg}\n{call}\n"
