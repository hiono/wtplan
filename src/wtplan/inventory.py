from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

DEFAULT_INVENTORY: dict[str, Any] = {
    "version": 1,
    "root": ".",
    "bare_dir": "bare",
    "workspaces_dir": "worktrees",
    "default_policy": {
        "exclude": {"from_links": True, "always": []},
        "links_repo_root": {"type": "symlink", "force": False, "delete": False},
    },
    "presets": {},
    "links_repo_root": [],
    "workspaces": {},
}


@dataclass(frozen=True)
class InventoryPaths:
    root: Path
    bare_dir: Path
    workspaces_dir: Path


def load_inventory(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Inventory must be a mapping")
    return data


def write_inventory(path: Path, data: dict[str, Any]) -> None:
    text = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    path.write_text(text, encoding="utf-8")


def resolve_paths(inv: dict[str, Any], base_dir: Path) -> InventoryPaths:
    root = (base_dir / str(inv.get("root", "."))).resolve()
    return InventoryPaths(
        root=root,
        bare_dir=(root / str(inv.get("bare_dir", "bare"))).resolve(),
        workspaces_dir=(root / str(inv.get("workspaces_dir", "worktrees"))).resolve(),
    )
