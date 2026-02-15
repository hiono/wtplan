from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from .inventory import DEFAULT_INVENTORY, resolve_paths, write_inventory
from .policy import LinkPolicy, per_link_policy

INVENTORY_FILE = ".wtplan.yml"


@dataclass(frozen=True)
class PlanItem:
    kind: str  # NOOP|ADD|UPDATE|DELETE|CONFLICT
    target: str
    detail: str


def ensure_inventory(base_dir: Path, toolbox_dir: str | None = None) -> Path:
    inv_path = base_dir / INVENTORY_FILE
    if inv_path.exists():
        return inv_path
    inv = dict(DEFAULT_INVENTORY)
    if toolbox_dir:
        inv["toolbox_dir"] = toolbox_dir
    write_inventory(inv_path, inv)
    return inv_path


def init_workspace_layout(inv: dict, base_dir: Path) -> dict[str, str]:
    paths = resolve_paths(inv, base_dir)
    paths.bare_dir.mkdir(parents=True, exist_ok=True)
    paths.workspaces_dir.mkdir(parents=True, exist_ok=True)
    return {
        "root": str(paths.root),
        "bare_dir": str(paths.bare_dir),
        "workspaces_dir": str(paths.workspaces_dir),
    }


def compute_workspace_id(repo_upper: str, iid: int) -> str:
    return f"{repo_upper}_ISSUE_{iid:04d}"


def workspace_path(inv: dict, base_dir: Path, preset: str | None, iid: int | None, repo: str | None) -> Path:
    presets = inv.get("presets") or {}

    # Single repo mode: when preset is None
    if preset is None:
        primary = repo or "default"
        alias = repo or primary
        repo_upper = primary.upper()
        ws_id = compute_workspace_id(repo_upper, iid or 0)
        paths = resolve_paths(inv, base_dir)
        return paths.workspaces_dir / ws_id / alias

    # Preset mode
    p = presets.get(preset)
    if not p:
        raise KeyError(f"Unknown preset: {preset}")
    primary = str(p.get("primary_repo"))
    alias = repo or primary
    repo_upper = primary.upper()
    ws_id = compute_workspace_id(repo_upper, iid or 0)
    paths = resolve_paths(inv, base_dir)
    return paths.workspaces_dir / ws_id / alias


def plan_links(inv: dict, base_dir: Path, policy: LinkPolicy) -> list[PlanItem]:
    toolbox_dir = inv.get("toolbox_dir")
    if not toolbox_dir:
        return []
    tb = Path(str(toolbox_dir)).resolve()
    if not tb.exists():
        return [PlanItem("CONFLICT", str(tb), "toolbox_dir does not exist")]

    items = inv.get("links_repo_root") or []
    if not isinstance(items, list):
        raise ValueError("links_repo_root must be a list")

    plan: list[PlanItem] = []
    for it in items:
        if not isinstance(it, dict):
            plan.append(PlanItem("CONFLICT", "<unknown>", "invalid link item"))
            continue
        source = str(it.get("source"))
        target = str(it.get("target", Path(source).name))
        p = per_link_policy(it, policy)
        src = tb / source
        dst = (base_dir / target).resolve()

        if not src.exists():
            plan.append(PlanItem("CONFLICT", str(dst), f"missing source: {src}"))
            continue

        if not dst.exists():
            plan.append(PlanItem("ADD", str(dst), f"{p.type} from {src}"))
            continue

        if p.type == "symlink":
            if dst.is_symlink() and dst.resolve() == src.resolve():
                plan.append(PlanItem("NOOP", str(dst), "already linked"))
            else:
                plan.append(
                    PlanItem(
                        "UPDATE" if p.force else "CONFLICT",
                        str(dst),
                        "replace existing with symlink" if p.force else "existing differs",
                    )
                )
        else:
            same = False
            try:
                if src.is_file() and dst.is_file():
                    same = src.stat().st_size == dst.stat().st_size
            except OSError:
                same = False
            if same:
                plan.append(PlanItem("NOOP", str(dst), "already copied (shallow match)"))
            else:
                plan.append(PlanItem("UPDATE" if p.force else "CONFLICT", str(dst), "copy update"))
                if p.delete:
                    msg = "delete extra files (rsync -a --delete)"
                    plan.append(PlanItem("DELETE", str(dst), msg))

    return plan


def apply_links(inv: dict, base_dir: Path, policy: LinkPolicy) -> list[PlanItem]:
    toolbox_dir = inv.get("toolbox_dir")
    if not toolbox_dir:
        return []
    tb = Path(str(toolbox_dir)).resolve()

    items = inv.get("links_repo_root") or []
    out: list[PlanItem] = []

    for it in items:
        if not isinstance(it, dict):
            continue
        source = str(it.get("source"))
        target = str(it.get("target", Path(source).name))
        p = per_link_policy(it, policy)
        src = tb / source
        dst = (base_dir / target).resolve()
        dst.parent.mkdir(parents=True, exist_ok=True)

        if not src.exists():
            out.append(PlanItem("CONFLICT", str(dst), f"missing source: {src}"))
            continue

        if dst.exists() or dst.is_symlink():
            if p.type == "symlink" and dst.is_symlink() and dst.resolve() == src.resolve():
                out.append(PlanItem("NOOP", str(dst), "already linked"))
                continue
            if not p.force:
                out.append(PlanItem("CONFLICT", str(dst), "existing differs (use --force-links)"))
                continue
            if dst.is_dir() and not dst.is_symlink():
                shutil.rmtree(dst)
            else:
                dst.unlink(missing_ok=True)

        if p.type == "symlink":
            dst.symlink_to(src)
            out.append(PlanItem("ADD", str(dst), f"symlink -> {src}"))
        else:
            if src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True)
                out.append(PlanItem("ADD", str(dst), "copied dir (rsync -a like)"))
                if p.delete:
                    _sync_delete_extra(src, dst)
                    out.append(PlanItem("DELETE", str(dst), "deleted extras (rsync -a --delete)"))
            else:
                shutil.copy2(src, dst)
                out.append(PlanItem("ADD", str(dst), "copied file"))

    return out


def _sync_delete_extra(src: Path, dst: Path) -> None:
    src_entries = {p.name for p in src.iterdir()} if src.exists() else set()
    for p in dst.iterdir():
        if p.name not in src_entries:
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink(missing_ok=True)
        else:
            sp = src / p.name
            if sp.is_dir() and p.is_dir():
                _sync_delete_extra(sp, p)
