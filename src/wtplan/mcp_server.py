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
    """Inventory 初期化、bare 準備、（任意）toolbox 有効化。"""
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
    """inventory と実体の差分（作成/削除/更新）を要約。"""
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
    """preset + Issue IID から workspace を作成（plan→confirm→apply）。"""
    base_dir = Path.cwd()
    inv = load_inventory(base_dir / ".wtplan.yml")
    pol = effective_policy(inv, cli_force=bool(force_links), cli_delete=bool(delete_links))
    planned = plan_links(inv, base_dir, pol)
    if not apply:
        return {"apply": False, "plan": [p.__dict__ for p in planned], "base": base}
    applied = apply_links(inv, base_dir, pol)
    return {"apply": True, "result": [p.__dict__ for p in applied], "base": base}


@mcp.tool(name="preset_rm")
def tool_preset_rm(
    preset: str,
    issue_iid: int,
    force: bool | None = False,
    apply: bool | None = False,
) -> dict[str, Any]:
    """preset + Issue IID から workspace をセーフ削除（v0.1 はスタブ）。"""
    return {
        "apply": bool(apply),
        "force": bool(force),
        "note": "safe delete (dirty/unpushed/diverged/unknown) is not implemented in v0.1",
        "preset": preset,
        "issue_iid": issue_iid,
    }


@mcp.tool(name="path")
def tool_path(preset: str, issue_iid: int, repo: str | None = None) -> dict[str, Any]:
    """workspace/repo の絶対パスを返す（参照専用）。"""
    base_dir = Path.cwd()
    inv = load_inventory(base_dir / ".wtplan.yml")
    p = workspace_path(inv, base_dir, preset=preset, iid=issue_iid, repo=repo)
    return {"path": str(p)}


@mcp.prompt(name="create_workspace_from_issue")
def prompt_create_workspace_from_issue(preset: str, issue_iid: int, base: str | None = None) -> str:
    b = base or ""
    args = f"preset: '{preset}', issue_iid: {issue_iid}, base: '{b}', apply: false"
    return (
        "Issue IID から workspace を作成。\n"
        "1) plan を取得（apply=false）\n"
        f"   tools/call: preset_add {{{args}}}\n"
        "2) plan を確認して問題なければ apply=true で実行\n"
        "   tools/call: preset_add {..., apply: true}\n"
    )


@mcp.prompt(name="review_workspace_plan")
def prompt_review_workspace_plan(workspace_id: str | None = None) -> str:
    return (
        "plan の内容を要約して、CONFLICT/UPDATE/DELETE を強調。\n"
        "特に delete-links（rsync -a --delete 相当）を伴う場合は破壊的変更として注意喚起。\n"
    )


@mcp.prompt(name="safe_remove_workspace")
def prompt_safe_remove_workspace(preset: str, issue_iid: int) -> str:
    msg = "workspace 削除前に状態を確認（dirty/unpushed/diverged/unknown）して、force の是非を問いかける。"
    args = f"preset: '{preset}', issue_iid: {issue_iid}, force: false, apply: false"
    call = f"tools/call: preset_rm {{{args}}}"
    return f"{msg}\n{call}\n"
