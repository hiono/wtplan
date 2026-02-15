from __future__ import annotations

import argparse
from pathlib import Path

from rich.console import Console

from .core import ensure_inventory, workspace_path
from .inventory import load_inventory
from .mcp_server import mcp, tool_plan

console = Console()


def _cmd_init(args: argparse.Namespace) -> int:
    ensure_inventory(Path.cwd(), toolbox_dir=args.toolbox)
    inv = load_inventory(Path.cwd() / ".wtplan.yml")
    console.print("Initialized .wtplan.yml", style="green")
    if args.toolbox:
        console.print(f"toolbox_dir: {args.toolbox}")
    console.print(inv)
    return 0


def _cmd_completion(args: argparse.Namespace) -> int:
    if args.shell != "bash":
        console.print("Only bash completion is provided in v0.1", style="yellow")
        return 0

    script = """
_wtplan_completions() {
  local cur
  COMPREPLY=()
  cur="${COMP_WORDS[COMP_CWORD]}"
  local cmds="init plan preset path cd completion"
  if [[ ${COMP_CWORD} -eq 1 ]]; then
    COMPREPLY=( $(compgen -W "${cmds}" -- "${cur}") )
    return 0
  fi
}
complete -F _wtplan_completions wtplan
"""
    print(script.strip())
    return 0


def _cmd_cd(args: argparse.Namespace) -> int:
    inv = load_inventory(Path.cwd() / ".wtplan.yml")
    p = workspace_path(inv, Path.cwd(), preset=args.preset, iid=args.iid, repo=args.repo)
    s = str(p).replace("'", "'''")
    if args.with_tool:
        print(f"cd '{s}' && {args.with_tool} .")
    else:
        print(f"cd '{s}'")
    return 0


def _cmd_path(args: argparse.Namespace) -> int:
    inv = load_inventory(Path.cwd() / ".wtplan.yml")
    p = workspace_path(inv, Path.cwd(), preset=args.preset, iid=args.iid, repo=args.repo)
    print(str(p))
    return 0


def _cmd_plan(args: argparse.Namespace) -> int:
    res = tool_plan(workspace_id=args.workspace_id)
    console.print_json(data=res)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="wtplan")
    sub = p.add_subparsers(dest="cmd")

    p_init = sub.add_parser("init")
    p_init.add_argument("--toolbox", default=None)
    p_init.set_defaults(func=_cmd_init)

    p_comp = sub.add_parser("completion")
    p_comp.add_argument("shell", choices=["bash", "zsh", "fish", "pwsh"], default="bash")
    p_comp.set_defaults(func=_cmd_completion)

    p_cd = sub.add_parser("cd")
    p_cd.add_argument("preset")
    p_cd.add_argument("iid", type=int)
    p_cd.add_argument("--repo", default=None)
    p_cd.add_argument("--with", dest="with_tool", default=None)
    p_cd.set_defaults(func=_cmd_cd)

    p_path = sub.add_parser("path")
    p_path.add_argument("preset")
    p_path.add_argument("iid", type=int)
    p_path.add_argument("--repo", default=None)
    p_path.set_defaults(func=_cmd_path)

    p_plan = sub.add_parser("plan")
    p_plan.add_argument("--workspace-id", default=None)
    p_plan.set_defaults(func=_cmd_plan)

    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.cmd:
        mcp.run()
        return

    raise SystemExit(args.func(args))
